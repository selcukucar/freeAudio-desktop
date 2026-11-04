# -*- coding: utf-8 -*-
# freeAudio - Small independent config toggles: mute notifications,
# track-change announcements/voice, save-liked-songs
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._dialog (defined elsewhere
# on GlobalPlugin) is used as a normal instance attribute via the class's
# MRO, no import needed for it.
#
# None of these scripts has a default gesture (all are bound manually via
# NVDA's Input Gestures dialog), so - unlike every other mixin extracted
# so far - nothing needs to be added to GlobalPlugin's __gestures dict.

import config
import ui
from scriptHandler import script

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from .settingsPanel import freeAudioSettingsPanel


class MiscTogglesMixin:
	"""Standalone on/off config toggles that don't fit any other mixin:
	mute notifications, auto-announce track changes (and its
	voice), and saving liked songs to a text file."""

	@script(
		# Translators: Name of an NVDA command; mutes/unmutes all of freeAudio's spoken notifications (station changes, playback state, recording, volume level) at once.
		description=_("Toggle mute notifications (station changes, playback, recording, volume level)"),
		category=_("freeAudio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleMuteNotifications(self, gesture):
		current = config.conf["freeAudio"].get("mute_notifications", False)
		config.conf["freeAudio"]["mute_notifications"] = not current
		if not current:
			# Notifications are now muted — speak this final confirmation before silencing.
			# Translators: Spoken once, right before notifications go silent, to confirm the toggle happened (further notifications are suppressed after this).
			ui.message(_("Notifications muted"))
		else:
			# Translators: Spoken when notifications are turned back on.
			ui.message(_("Notifications unmuted"))



	@script(
		# Translators: Name of an NVDA command; toggles whether freeAudio announces a station's track/song changes from ICY stream metadata.
		description=_("Enable or disable auto-announce track changes (ICY metadata)"),
		category=_("freeAudio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleAnnounceTrackChanges(self, gesture):
		current = config.conf["freeAudio"].get("announce_track_changes", False)
		config.conf["freeAudio"]["announce_track_changes"] = not current

		# Keep the settings panel's checkbox and voice choice in sync if it's open.
		# freeAudioSettingsPanel._instance is the live panel itself (see
		# settingsPanel.py) - not self._dialog, which is the unrelated
		# RadioDialog browse window and never has these controls, so the
		# hasattr() below used to always be False and this sync never ran.
		panel = freeAudioSettingsPanel._instance
		if panel is not None and hasattr(panel, "_announce_track_changes"):
			try:
				panel._announce_track_changes.SetValue(not current)
				if hasattr(panel, "_track_change_voice"):
					panel._track_change_voice.Enable(not current)
			except Exception:
				pass

		# Translators: Announcement after toggling; %(effect)s is the plain-text feature name below (with its '&' access-key marker stripped), %(state)s is 'enabled'/'disabled'.
		ui.message(_("%(effect)s %(state)s") % {
			# Translators: Feature name reused as both the settings-panel checkbox label (with '&' marking its access key) and, with the '&' stripped, as %(effect)s in the toggle announcement above.
			"effect": _("&Auto-announce track changes (ICY metadata)").replace("&", ""),
			# Translators: Second half of the toggle announcement above; describes the feature's new on/off state.
			"state": _("enabled") if not current else _("disabled"),
		})

	@script(
		# Translators: Name of an NVDA command; switches which voice (NVDA's current synth, or a separate SAPI5 voice) speaks track-change announcements.
		description=_("Switch track change announcement voice"),
		category=_("freeAudio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_switchTrackChangeVoice(self, gesture):
		current = config.conf["freeAudio"].get("track_change_voice", "screen_reader")
		new_value = "sapi5" if current != "sapi5" else "screen_reader"
		config.conf["freeAudio"]["track_change_voice"] = new_value

		# Keep the settings panel's voice choice in sync if it's open.
		# See the matching comment in script_toggleAnnounceTrackChanges above.
		panel = freeAudioSettingsPanel._instance
		if panel is not None and hasattr(panel, "_track_change_voice"):
			try:
				panel._track_change_voice.SetSelection(0 if new_value != "sapi5" else 1)
			except Exception:
				pass

		ui.message(_("Windows voice (SAPI5)") if new_value == "sapi5" else _("Screen reader"))

	@script(
		# Translators: Name of an NVDA command; toggles whether liked/favourited songs are also appended to a plain text file on disk.
		description=_("Turn on or off saving liked songs to a text file"),
		category=_("freeAudio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleSaveLikedSongs(self, gesture):
		current = config.conf["freeAudio"].get("save_liked_songs", False)
		config.conf["freeAudio"]["save_liked_songs"] = not current

		# Keep the settings panel's checkbox in sync if it's open.
		# See the matching comment in script_toggleAnnounceTrackChanges above.
		panel = freeAudioSettingsPanel._instance
		if panel is not None and hasattr(panel, "_save_liked_songs"):
			try:
				panel._save_liked_songs.SetValue(not current)
			except Exception:
				pass

		# Translators: Same toggle-announcement pattern as script_toggleAnnounceTrackChanges above.
		ui.message(_("%(effect)s %(state)s") % {
			# Translators: Feature name for the save-liked-songs toggle, used the same way as the track-change one above (checkbox label with '&' access key, and %(effect)s with it stripped).
			"effect": _("&Save liked songs to a text file").replace("&", ""),
			# Translators: Second half of the toggle announcement; describes the feature's new on/off state.
			"state": _("enabled") if not current else _("disabled"),
		})
