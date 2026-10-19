function initializeSettlementDialogs(root = document) {
    root.querySelectorAll('[data-settlement-dialog]').forEach((dialog) => {
        const find = (name) => dialog.querySelector(`[data-${name}]`);
        const fullAmount = Number(dialog.dataset.fullAmount);
        const amountInput = find('settlement-amount');
        const form = find('settlement-form');
        const copyStatus = find('payment-copy-status');
        const isIOS = /iPad|iPhone|iPod/i.test(navigator.userAgent)
            || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
        const gpay = find('gpay-link');
        find('ios-payment-note').hidden = !isIOS;
        const upi = dialog.dataset.upiId || '';
        const validUPI = /^[a-zA-Z0-9._-]{2,}@[a-zA-Z0-9.-]{2,}$/.test(upi);


        function selectedAmount() {
            const raw = amountInput.value.trim();
            const value = Number(raw);
            return /^\d+(\.\d{1,2})?$/.test(raw) && value >= 0.01 && value <= fullAmount
                ? value.toFixed(2) : null;
        }
        function updateAmount() {
            const full = dialog.querySelector('input[type="radio"]:checked').value === 'full';
            amountInput.readOnly = full;
            if (full) amountInput.value = fullAmount.toFixed(2);
            const amount = selectedAmount();
            find('settlement-display').textContent = amount ? `₹${amount}` : 'Enter a valid amount';
            find('settlement-submit-amount').value = amount || '';
            copyStatus.textContent = '';
            gpay.hidden = isIOS || !validUPI;
            gpay.removeAttribute('href');
            if (!isIOS && validUPI && amount) {
                const params = Object.entries({pa: upi, pn: dialog.dataset.payeeName || upi, am: amount, cu: 'INR'})
                    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`).join('&');
                gpay.setAttribute('href', `intent://pay?${params}#Intent;scheme=upi;package=com.google.android.apps.nbu.paisa.user;S.browser_fallback_url=${encodeURIComponent(window.location.href.split('#')[0])};end`);
            }
            gpay.setAttribute('aria-disabled', String(!amount));

        }
        dialog.querySelectorAll('input[type="radio"]').forEach((mode) => mode.addEventListener('change', updateAmount));
        amountInput.addEventListener('input', updateAmount);
        find('settlement-copy-amount').addEventListener('click', async () => {
            const amount = selectedAmount();
            if (!amount) { amountInput.focus(); return; }
            try {
                await navigator.clipboard.writeText(amount);
                copyStatus.textContent = 'Amount copied. Verify it in your payment app before paying.';
            } catch {
                copyStatus.textContent = `Copy this amount manually: ₹${amount}`;
            }
        });
        gpay.addEventListener('click', (event) => {
            if (isIOS || !validUPI || !selectedAmount()) event.preventDefault();
            // Launch/return never records payment; only the explicit paid form does.
        });
        form.addEventListener('submit', (event) => {
            if (!selectedAmount()) { event.preventDefault(); amountInput.focus(); }
        });
        updateAmount();
    });
}

initializeSettlementDialogs();

if (document.querySelector('[data-group-live]')) {
    let generation = 0;
    let refreshing = false;
    let saving = false;
    const notice = document.querySelector('[data-group-live-notice]');

    function showNotice(message) {
        if (!notice) return;
        notice.textContent = message;
        notice.hidden = !message;
    }

    async function refreshGroup(force = false) {
        if (!force && (saving || refreshing || document.hidden)) return;
        const current = document.querySelector('[data-group-live]');
        if (!current) return;
        const requestGeneration = ++generation;
        refreshing = true;
        try {
            const response = await fetch(current.dataset.groupRefreshUrl, {
                credentials: 'same-origin', cache: 'no-store',
            });
            if (!response.ok) throw new Error('Could not refresh group balances. Try again.');
            const page = new DOMParser().parseFromString(await response.text(), 'text/html');
            if (requestGeneration !== generation) return;
            const next = page.querySelector('[data-group-live]');
            if (!next) throw new Error('Sign in again to refresh this group.');
            if (next.dataset.groupRevision === current.dataset.groupRevision) return;
            // Preserve expanded activity cards, but invalidate any open payment
            // dialog whose amount/recipient may now be out of date.
            const openCards = new Set(Array.from(current.querySelectorAll('[data-activity-key][open]'),
                (card) => card.dataset.activityKey));
            const openDialog = current.querySelector('dialog[open]');
            if (openDialog) {
                openDialog.close();
                if (!force) showNotice('Group payment details changed. Review the receiver and amount before paying.');
            } else if (!force) {
                showNotice('Group updated. Balances and payment statuses refreshed.');
            }
            next.querySelectorAll('[data-activity-key]').forEach((card) => {
                card.open = openCards.has(card.dataset.activityKey);
            });
            current.replaceWith(next);
            initializeSettlementDialogs(next);
        } catch (error) {
            if (force) throw error;
        } finally {
            if (requestGeneration === generation) refreshing = false;
        }
    }

    document.addEventListener('submit', async (event) => {
        const form = event.target.closest('form[data-group-action]');
        if (!form || event.defaultPrevented) return;
        event.preventDefault();
        if (saving) return;
        saving = true;
        ++generation; // Discard a poll that started before this write.
        const buttons = form.querySelectorAll('button');
        buttons.forEach((button) => { button.disabled = true; });
        showNotice('Saving payment…');
        try {
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
                headers: {'X-Requested-With': 'XMLHttpRequest'},
            });
            const result = await response.json();
            await refreshGroup(true);
            showNotice(result.message || (response.ok ? 'Payment saved.' : 'Could not save payment.'));
        } catch (error) {
            showNotice('Could not update this group. Check your connection and try again.');
        } finally {
            saving = false;
            refreshing = false;
            buttons.forEach((button) => { button.disabled = false; });
        }
    });

    window.setInterval(() => refreshGroup(), 5000);
    window.addEventListener('focus', () => refreshGroup());
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) refreshGroup();
    });
}
