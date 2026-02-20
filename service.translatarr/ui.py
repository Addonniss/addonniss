# -*- coding: utf-8 -*-
import xbmcgui, xbmcaddon

ADDON = xbmcaddon.Addon('service.translatarr')
DIALOG = xbmcgui.Dialog()

def notify(msg, title="Translatarr", duration=3000):
    DIALOG.notification(title, msg, xbmcgui.NOTIFICATION_INFO, duration)

def show_stats_box(src_file, trg_file, trg_name, cost, tokens, chunks, chunk_size):
    # Box Drawing Characters for the final "Cassette" look
    nl = "\n"
    header = "╔══════════════════════════════════════════╗"
    sep    = "╠══════════════════════════════════════════╣"
    footer = "╚══════════════════════════════════════════╝"
    
    # We truncate long filenames so they don't break the box
    src_display = (src_file[:30] + '..') if len(src_file) > 32 else src_file
    trg_display = (trg_file[:30] + '..') if len(trg_file) > 32 else trg_file
    
    body = [
        header,
        f"║           TRANSLATION COMPLETE           ║",
        sep,
        f"║ SOURCE: {src_display:<32} ║",
        f"║ TARGET: {trg_display:<32} ║",
        sep,
        f"║ LANGUAGE: {trg_name:<30} ║",
        f"║ CHUNKS:   {chunks:<4} (Size: {chunk_size:<3})              ║",
        sep,
        f"║ TOTAL TOKENS: {tokens:<26,} ║",
        f"║ TOTAL COST:   ${cost:<25.4f} ║",
        footer
    ]
    
    DIALOG.textviewer("Translatarr AI Stats", nl.join(body), usemono=True)

class TranslationProgress:
    def __init__(self, use_notifications, title='[B][COLOR gold]Translatarr AI[/COLOR][/B]'):
        self.use_notifications = use_notifications
        self.pDialog = None
        if not self.use_notifications:
            self.pDialog = xbmcgui.DialogProgress()
            self.pDialog.create(title, 'Initializing...')

    def update(self, percent, src_name, trg_name, chunk_num, total_chunks, lines_done, total_lines):
        if self.use_notifications:
            return
        
        # Dashboard Style Progress
        # Line 1: Filenames
        # Line 2: Chunk Status
        # Line 3: Line Count
        line1 = f"[COLOR gold]Source:[/COLOR] {src_name}"
        line2 = f"[COLOR gold]Target:[/COLOR] {trg_name}"
        line3 = f"Processing Chunk [B]{chunk_num}/{total_chunks}[/B] ({lines_done:,}/{total_lines:,} lines)"
        
        # In Kodi's DialogProgress.update(), you can pass 3 lines of text
        self.pDialog.update(percent, f"{line1}\n{line2}\n{line3}")

    def is_canceled(self):
        return self.pDialog.iscanceled() if self.pDialog else False

    def close(self):
        if self.pDialog:
            self.pDialog.close()
