# -*- coding: utf-8 -*-
"""One-time import of a previous FreeRadio installation's data into freeAudio.

freeAudio is the renamed successor of FreeRadio. Because the old add-on is
being removed from the NVDA add-on store, it can't ship a final "please
migrate" update, so the new add-on does the hand-over itself on first start:

* data files/folders in NVDA's config folder named freeradio* are COPIED to
  freeAudio* (never moved, so an old install that is still present keeps
  working until the user removes it);
* the old add-on's section in nvda.ini is read and its values are copied into
  the freeAudio section (only keys freeAudio knows about, and only if the user
  hasn't already set them in freeAudio);
* if the old default recordings folder exists and the user hadn't chosen a
  folder, freeAudio keeps using it instead of silently starting an empty one;
* if the old add-on is still installed, the user is told to remove it, since
  both would fight over the same shortcuts and audio device.

Not migrated: custom shortcuts the user assigned in NVDA's Input Gestures
dialog (NVDA stores those per add-on module path, so they don't carry over).
"""

import logging
import os
import shutil

import addonHandler
import config
import globalVars
import gui
import wx

addonHandler.initTranslation()

log = logging.getLogger(__name__)

_NEW_SECTION = "freeAudio"
# Section names the old add-on may have used in nvda.ini (ConfigObj keys are
# case-sensitive, so list every spelling that could exist).
_OLD_SECTIONS = ("freeRadio", "freeradio", "FreeRadio")
# Old add-on ID (manifest "name"), compared case-insensitively.
_OLD_ADDON_NAMES = ("freeradio",)
# Data-file prefixes, compared case-insensitively / used for the new name.
_OLD_FILE_PREFIX = "freeradio"
_NEW_FILE_PREFIX = "freeAudio"
# Transient files that must never be carried over.
_SKIP_SUFFIXES = (".tmp", ".lock", ".buf")
# Folders bigger than this are left behind rather than copied synchronously
# during NVDA startup (e.g. a large audio cache).
_MAX_DIR_BYTES = 50 * 1024 * 1024
_OLD_RECORDINGS_DIR_NAME = "freeradio recordings"
_NEW_RECORDINGS_DIR_NAME = "freeAudio Recordings"


def _dir_size(path):
	total = 0
	for root, _dirs, files in os.walk(path):
		for f in files:
			try:
				total += os.path.getsize(os.path.join(root, f))
			except OSError:
				pass
	return total


def _remove_partial(path):
	try:
		if os.path.isdir(path):
			shutil.rmtree(path, ignore_errors=True)
		elif os.path.exists(path):
			os.remove(path)
	except OSError:
		pass


def _migrate_files():
	"""Copy freeradio* entries in the config folder to their freeAudio* twins.

	Skips anything whose destination already exists, so it can never
	overwrite data the user already has in freeAudio. Returns the list of
	copied names.
	"""
	base = globalVars.appArgs.configPath
	copied = []
	try:
		names = os.listdir(base)
	except OSError:
		return copied
	for name in names:
		lower = name.lower()
		if not lower.startswith(_OLD_FILE_PREFIX) or lower.endswith(_SKIP_SUFFIXES):
			continue
		src = os.path.join(base, name)
		dst = os.path.join(base, _NEW_FILE_PREFIX + name[len(_OLD_FILE_PREFIX):])
		if os.path.exists(dst):
			continue
		try:
			if os.path.isdir(src):
				if _dir_size(src) > _MAX_DIR_BYTES:
					log.info("freeAudio: not copying large legacy folder %s", name)
					continue
				shutil.copytree(src, dst)
			else:
				shutil.copy2(src, dst)
			copied.append(name)
		except (OSError, shutil.Error):
			log.warning("freeAudio: could not copy legacy data %s", name, exc_info=True)
			_remove_partial(dst)
	return copied


def _migrate_settings():
	"""Copy known keys from the old add-on's nvda.ini section. Returns the count."""
	from configobj.validate import Validator

	# Read the raw base profile: once the old add-on is uninstalled its
	# section is no longer in NVDA's spec, so config.conf["freeRadio"]
	# would raise, but the values are still stored in the profile.
	base_profile = config.conf.profiles[0]
	old = None
	for name in _OLD_SECTIONS:
		candidate = base_profile.get(name)
		if candidate is not None and hasattr(candidate, "items"):
			old = candidate
			break
	if old is None:
		return 0
	new_spec = config.conf.spec[_NEW_SECTION]
	already_set = base_profile.get(_NEW_SECTION) or {}
	new_section = config.conf[_NEW_SECTION]
	validator = Validator()
	migrated = 0
	for key, raw in old.items():
		if hasattr(raw, "items") or key not in new_spec or key in already_set:
			continue
		try:
			new_section[key] = validator.check(new_spec[key], raw)
			migrated += 1
		except Exception:
			log.debug("freeAudio: skipped legacy setting %s", key, exc_info=True)
	return migrated


def _adopt_old_recordings_folder():
	"""Keep using the old default recordings folder if the user never picked one."""
	section = config.conf[_NEW_SECTION]
	if section.get("recordings_dir"):
		return
	docs = os.path.join(os.path.expanduser("~"), "Documents")
	if os.path.isdir(os.path.join(docs, _NEW_RECORDINGS_DIR_NAME)):
		return
	try:
		names = os.listdir(docs)
	except OSError:
		return
	for name in names:
		path = os.path.join(docs, name)
		if name.lower() == _OLD_RECORDINGS_DIR_NAME and os.path.isdir(path):
			section["recordings_dir"] = path
			return


def _find_old_addon():
	try:
		for addon in addonHandler.getAvailableAddons():
			name = str(addon.manifest.get("name", "")).lower()
			if name in _OLD_ADDON_NAMES and not getattr(addon, "isPendingRemove", False):
				return addon
	except Exception:
		log.debug("freeAudio: could not list add-ons", exc_info=True)
	return None


def _warn_old_addon_still_installed():
	def _show():
		gui.messageBox(
			# Translators: Shown when the previous version of this add-on (FreeRadio) is still installed next to freeAudio.
			_(
				"The previous version of this add-on, FreeRadio, is still installed alongside freeAudio. "
				"Running both at the same time makes them compete for the same shortcuts and audio device. "
				"Your settings and data have been copied to freeAudio. "
				"Please uninstall FreeRadio (NVDA menu, Tools, Add-on Store or Manage add-ons) and restart NVDA."
			),
			# Translators: Title of the warning about the old FreeRadio add-on still being installed.
			_("freeAudio"),
			wx.OK | wx.ICON_WARNING,
		)

	# Give NVDA's main window time to finish starting up first.
	wx.CallLater(4000, _show)


def run():
	"""Entry point: call once from GlobalPlugin.__init__, before the player
	and the managers read config or data files."""
	section = config.conf[_NEW_SECTION]
	if not section.get("legacy_migrated", False):
		try:
			files = _migrate_files()
			settings = _migrate_settings()
			_adopt_old_recordings_folder()
			log.info(
				"freeAudio: legacy import done (%d data entries, %d settings)",
				len(files), settings,
			)
		except Exception:
			log.error("freeAudio: legacy import failed", exc_info=True)
		# Set the flag even after a failure: a retry could overwrite
		# settings the user has changed since.
		section["legacy_migrated"] = True
	if _find_old_addon() is not None:
		_warn_old_addon_still_installed()
