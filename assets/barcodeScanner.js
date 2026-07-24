if (!window.dash_clientside) { window.dash_clientside = {}; }

function isKeyboardInput(document) {
    focused = document.activeElement
    return (focused.activeElement && (
        focused.tagName === "INPUT" ||
        focused.tagName === "TEXTAREA" ||
        focused.tagName === "SELECT" ||
        focused.isContentEditable))
}

window.dash_clientside.helper = {
    initScanner: function(id, modalNeuerEintragOpen, modalStammdatenOpen) {
        // Always update modal states so onScan can read the latest values
        window._modalNeuerEintragOpen = modalNeuerEintragOpen;
        window._modalStammdatenOpen = modalStammdatenOpen;

        if (window._onScanAttached) return window.dash_clientside.no_update;

        function init() {
            if (typeof onScan === 'undefined') {
                setTimeout(init, 100);
                return;
            }

            onScan.attachTo(document, {
                suffixKeyCodes: [13],
                minLength: 5,
                avgTimeByChar: 20,

                onKeyDetect: function(iKeyCode, oEvent) {
                    // Suppress Enter during scan to prevent form submissions
                    if (iKeyCode === 13 && onScan.isScanInProgressFor(document)) {
                        oEvent.preventDefault();
                        oEvent.stopImmediatePropagation();
                    }
                },

                onScan: function(sCode) {
                    const modalOpen = window._modalNeuerEintragOpen || window._modalStammdatenOpen;

                    if (modalOpen) {
                        // Modal is open: let the scan input stay in the focused field as-is
                        return;

                    }
                    if (isKeyboardInput(document)) {
                        const start = focused.selectionStart;
                        focused.setSelectionRange(start - sCode.length, start);
                        document.execCommand('delete');
                    }

                    // Fire the custom event for EventListener to catch
                    document.dispatchEvent(
                        new CustomEvent('scan', { detail: sCode, bubbles: true })
                    );
                }
            });

            window._onScanAttached = true;
        }

        init();
        return window.dash_clientside.no_update;
    },
};