# -*- coding: utf-8 -*-
import xbmcgui, xbmcaddon

ADDON = xbmcaddon.Addon('service.translatarr')
DIALOG = xbmcgui.Dialog()

def notify(msg, title="Translatarr", duration=3000):
    DIALOG.notification(title, msg, xbmcgui.NOTIFICATION_INFO, duration)

def show_stats_box(trg_name, cost, tokens):
    stats_msg = f"[B]Target:[/B] {trg_name}\n[B]Cost:[/B] ${cost:.4f}\n[B]Total Tokens:[/B] {tokens}"
    DIALOG.textviewer("Translation Success", stats_msg)

class TranslationProgress:
    def __init__(self, use_notifications, title='[B][COLOR gold]Translatarr AI[/COLOR][/B]'):
        self.use_notifications = use_notifications
        self.pDialog = None
        if not self.use_notifications:
            self.pDialog = xbmcgui.DialogProgress()
            self.pDialog.create(title, 'Initializing...')

    def update(self, percent, filename, chunk_num, total_chunks, lines_done, total_lines):
        if self.use_notifications:
            return # Don't update dialog if in notification mode
        
        msg = (f"[B]File:[/B] {filename}\n"
               f"[B]Action:[/B] Chunk {chunk_num} of {total_chunks}\n"
               f"[B]Status:[/B] {lines_done:,} / {total_lines:,} lines")
        self.pDialog.update(percent, msg)

    def is_canceled(self):
        return self.pDialog.iscanceled() if self.pDialog else False

    def close(self):
        if self.pDialog:
            self.pDialog.close()
