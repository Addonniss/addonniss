# -*- coding: utf-8 -*-
import xbmcgui, xbmcaddon

ADDON = xbmcaddon.Addon('service.translatarr')
DIALOG = xbmcgui.Dialog()

# -----------------------------------
# Notifications
# -----------------------------------

def notify(msg, title="Translatarr", duration=3000):
    DIALOG.notification(title, msg, xbmcgui.NOTIFICATION_INFO, duration)


# -----------------------------------
# Statistics Popup
# -----------------------------------

def show_stats_box(src_file, trg_file, trg_name, cost, tokens, chunks, chunk_size, model_name):

    # Provider Badge Color
    if "gemini" in model_name.lower():
        model_color = "mediumpurple"
    else:
        model_color = "deepskyblue"

    stats_msg = (
        "[B][COLOR gold]TRANSLATARR SUCCESS[/COLOR][/B]\n"
        "------------------------------------------------------------\n"
        f"[B]Source:[/B] [COLOR lightgray]{src_file}[/COLOR]\n"
        f"[B]Target:[/B] [COLOR lightgray]{trg_file}[/COLOR]\n"
        f"[B]Lang:[/B]   [COLOR lightblue]{trg_name}[/COLOR]\n"
        f"[B]Model:[/B]  [B][COLOR {model_color}]{model_name}[/COLOR][/B]\n\n"
        "[B][COLOR orange]USAGE DETAILS[/COLOR][/B]\n"
        "------------------------------------------------------------\n"
        f"[B]• Total Tokens:[/B]   [COLOR springgreen]{tokens:,}[/COLOR]\n"
        f"[B]• Total Chunks:[/B]   [COLOR springgreen]{chunks} (Size: {chunk_size})[/COLOR]\n"
        f"[B][COLOR gold]• Estimated Cost:[/COLOR][/B] "
        f"[B][COLOR gold]${cost:.4f}[/COLOR][/B]"
    )

    DIALOG.textviewer("Translatarr Statistics", stats_msg, usemono=False)


# -----------------------------------
# Progress Dialog
# -----------------------------------

class TranslationProgress:

    def __init__(self, use_notifications, title='[B][COLOR gold]Translatarr[/COLOR][/B]'):
        self.use_notifications = use_notifications
        self.title = title
        self.pDialog = None

        if not self.use_notifications:
            self.pDialog = xbmcgui.DialogProgress()
            self.pDialog.create(title, 'Initializing...')
        else:
            notify("Background Translation Started...")

    # -----------------------------------

    def _build_bar(self, percent, width=10):
        filled = int(width * percent / 100)
        empty = width - filled
        return "█" * filled + "░" * empty

    # -----------------------------------

    def update(self, percent, src_name, trg_name,
               chunk_num, total_chunks, lines_done, total_lines):

        bar = self._build_bar(percent)
        bar_line = f"[B]{bar}[/B] {percent}%"

        # Stealth Mode (notifications)
        if self.use_notifications:
            if chunk_num % 2 == 0 or chunk_num == total_chunks:
                msg = f"{bar_line} ({chunk_num}/{total_chunks} chunks)"
                notify(msg, title=self.title, duration=2000)
            return

        # Dialog Mode
        if self.pDialog:
            line1 = f"[COLOR gold]Source:[/COLOR] {src_name}"
            line2 = f"[COLOR gold]Target:[/COLOR] {trg_name}"
            line3 = f"Chunk [B]{chunk_num}/{total_chunks}[/B] • {lines_done:,}/{total_lines:,} lines"
            line4 = f"\n{bar_line}"

            self.pDialog.update(
                percent,
                f"{line1}\n{line2}\n{line3}\n{line4}"
            )

    # -----------------------------------

    def is_canceled(self):
        if self.use_notifications or self.pDialog is None:
            return False
        return self.pDialog.iscanceled()

    # -----------------------------------

    def close(self):
        if self.pDialog:
            self.pDialog.close()
            self.pDialog = None
