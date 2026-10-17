document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('split-bill-form');
    if (!form) return;

    const totalInput = form.querySelector('[name="amount"]');
    const rows = [...form.querySelectorAll('[data-member-row]')];
    const count = document.getElementById('split-bill-selected-count');
    const totalLabel = document.getElementById('split-bill-total-label');
    const totalValue = document.getElementById('split-bill-total-value');
    const guidance = document.getElementById('split-bill-guidance');
    const money = new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    function update() {
        const mode = form.querySelector('[name="split_method"]:checked')?.value || 'equal';
        const selected = rows.filter((row) => row.querySelector('[type="checkbox"]').checked);
        const totalCents = Math.round(Number(totalInput.value || 0) * 100);
        count.textContent = `${selected.length} of ${rows.length} selected`;

        rows.forEach((row) => {
            const included = row.querySelector('[type="checkbox"]').checked;
            const percentInput = row.querySelector('[name^="percent_"]');
            const amountInput = row.querySelector('[name^="amount_"]');
            row.classList.toggle('is-excluded', !included);
            row.querySelector('[data-equal-value]').hidden = mode !== 'equal';
            row.querySelector('[data-percentage-value]').hidden = mode !== 'percentage';
            row.querySelector('[data-amount-value]').hidden = mode !== 'amount';
            percentInput.disabled = mode !== 'percentage' || !included;
            amountInput.disabled = mode !== 'amount' || !included;
            const equalValue = row.querySelector('[data-equal-value]');
            if (!included || !selected.length || !Number.isFinite(totalCents) || totalCents < 0) {
                equalValue.textContent = 'Not included';
            } else {
                const index = selected.indexOf(row);
                const cents = Math.floor(totalCents / selected.length) + (index < totalCents % selected.length ? 1 : 0);
                equalValue.textContent = `₹${money.format(cents / 100)}`;
            }
        });

        if (mode === 'equal') {
            totalLabel.textContent = 'Split equally between';
            totalValue.textContent = `${selected.length} ${selected.length === 1 ? 'person' : 'people'}`;
            guidance.textContent = selected.length ? 'Any leftover paisa is assigned to the first selected person.' : 'Tick at least one person.';
        } else {
            const entered = selected.reduce((sum, row) => {
                const input = row.querySelector(mode === 'percentage' ? '[name^="percent_"]' : '[name^="amount_"]');
                return sum + (Number(input.value) || 0);
            }, 0);
            const target = mode === 'percentage' ? 100 : totalCents / 100;
            totalLabel.textContent = mode === 'percentage' ? 'Percent allocated' : 'Amount allocated';
            totalValue.textContent = mode === 'percentage' ? `${entered.toFixed(2)} / 100%` : `₹${money.format(entered)} / ₹${money.format(target || 0)}`;
            guidance.textContent = mode === 'percentage'
                ? 'Selected percentages must total exactly 100%.'
                : 'Selected amounts must match the bill total exactly.';
        }
    }

    form.addEventListener('input', update);
    form.addEventListener('change', update);
    update();
});
