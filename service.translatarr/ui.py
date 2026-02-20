# -*- coding: utf-8 -*-
import xbmcgui, xbmcaddon

ADDON = xbmcaddon.Addon('service.translatarr')
DIALOG = xbmcgui.Dialog()

def notify(msg, title="Translatarr", duration=3000):
    # Standard 3-second pop-up
    DIALOG.notification(title, msg, xbmcgui.NOTIFICATION_INFO, duration)

def show_stats_box(src_file, trg_file, trg_name, cost, tokens, chunks, chunk_size, model_name):
    stats_msg = (
        "[B][COLOR gold]TRANSLATARR SUCCESS[/COLOR][/B]\n"
        "------------------------------------------------------------\n"
        f"[B]Source:[/B] [COLOR lightgray]{src_file}[/COLOR]\n"
        f"[B]Target:[/B] [COLOR lightgray]{trg_file}[/COLOR]\n"
        f"[B]Lang:[/B]   [COLOR lightblue]{trg_name}[/COLOR]\n"
        f"[B]Model:[/B]  [COLOR lightblue]{model_name}[/COLOR]\n\n"
        "[B][COLOR orange]USAGE DETAILS[/COLOR][/B]\n"
        "------------------------------------------------------------\n"
        f"[B]• Total Tokens:[/B]   [COLOR springgreen]{tokens:,}[/COLOR]\n"
        f"[B]• Total Chunks:[/B]   [COLOR springgreen]{chunks} (Size: {chunk_size})[/COLOR]\n"
        f"[B][COLOR gold]• Estimated Cost:[/COLOR][/B] [B][COLOR gold]${cost:.4f}[/COLOR][/B]"
    )
    DIALOG.textviewer("Translatarr Statistics", stats_msg, usemono=False)

class TranslationProgress:
    def __init__(self, use_notifications, title='[B][COLOR gold]Translatarr[/COLOR][/B]'):
        self.use_notifications = use_notifications
        self.title = title
        self.pDialog = None
        if not self.use_notifications:
            self.pDialog = xbmcgui.DialogProgress()
            self.pDialog.create(title, 'Initializing...')
        else:
            # For Stealth mode, we notify once at the start
            notify("Background Translation Started...")

    def update(self, percent, src_name, trg_name, chunk_num, total_chunks, lines_done, total_lines):
        # Update every 2 chunks in Stealth mode
        if self.use_notifications:
            if chunk_num % 2 == 0 or chunk_num == total_chunks:
                msg = f"Progress: {percent}% ({chunk_num}/{total_chunks} chunks)"
                notify(msg, title=self.title, duration=2000)
            return
        
        # Standard Pro Mode update
        if self.pDialog:
            line1 = f"[COLOR gold]Source:[/COLOR] {src_name}"
            line2 = f"[COLOR gold]Target:[/COLOR] {trg_name}"
            line3 = f"Chunk [B]{chunk_num}/{total_chunks}[/B] • {lines_done:,}/{total_lines:,} lines"
            self.pDialog.update(percent, f"{line1}\n{line2}\n{line3}")

    def is_canceled(self):
        if self.use_notifications or self.pDialog is None:
            return False
        return self.pDialog.iscanceled()

    def close(self):
        if self.pDialog:
            self.pDialog.close()
            self.pDialog = None
