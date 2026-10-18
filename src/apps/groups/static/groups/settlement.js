document.querySelectorAll('[data-settlement-dialog]').forEach((dialog) => {
    const fullAmount = Number(dialog.dataset.fullAmount);
    const amountInput = dialog.querySelector('[data-settlement-amount]');
    const amountDisplay = dialog.querySelector('[data-settlement-display]');
    const submitAmount = dialog.querySelector('[data-settlement-submit-amount]');
    const form = dialog.querySelector('[data-settlement-form]');
    const modes = dialog.querySelectorAll('input[type="radio"]');
    const paymentLinks = dialog.querySelectorAll('[data-payment-link]');

    function selectedAmount() {
        const raw = amountInput.value.trim();
        const amount = Number(raw);
        return /^\d+(\.\d{1,2})?$/.test(raw) && amount >= 0.01 && amount <= fullAmount
            ? amount.toFixed(2)
            : null;
    }

    function updateAmount() {
        const full = dialog.querySelector('input[type="radio"]:checked').value === 'full';
        amountInput.readOnly = full;
        if (full) amountInput.value = fullAmount.toFixed(2);
        const amount = selectedAmount();
        amountDisplay.textContent = amount ? `₹${amount}` : 'Enter a valid amount';
        submitAmount.value = amount || '';
        paymentLinks.forEach((link) => {
            if (!amount) {
                link.removeAttribute('href');
                link.setAttribute('aria-disabled', 'true');
                return;
            }
            const url = new URL(link.dataset.baseHref);
            url.searchParams.set('am', amount);
            link.href = url.toString();
            link.removeAttribute('aria-disabled');
        });
    }

    modes.forEach((mode) => mode.addEventListener('change', updateAmount));
    amountInput.addEventListener('input', updateAmount);
    paymentLinks.forEach((link) => link.addEventListener('click', (event) => {
        if (!selectedAmount()) event.preventDefault();
    }));
    form.addEventListener('submit', (event) => {
        if (!selectedAmount()) {
            event.preventDefault();
            amountInput.focus();
        }
    });
    updateAmount();
});
