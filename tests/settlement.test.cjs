const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('src/apps/groups/static/groups/settlement.js', 'utf8');

// Small DOM fixture exercises the actual event handlers without a build dependency.
function fixture({clipboardFails = false, userAgent = 'Android', platform = 'Linux', touches = 0, upi = 'receiver@oksbi'} = {}) {
    function element(extra = {}) {
        return Object.assign({value: '', checked: false, dataset: {}, listeners: {}, attrs: {},
            addEventListener(name, fn) { this.listeners[name] = fn; },
            setAttribute(name, value) { this.attrs[name] = value; },
            removeAttribute(name) { delete this.attrs[name]; },
            focus() { this.focused = true; },
        }, extra);
    }
    const full = element({value: 'full'}), partial = element({value: 'partial'});
    let mode = full;
    const form = element();
    const fields = {
        'settlement-amount': element({value: '100.00'}), 'settlement-form': form,
        'payment-copy-status': element(), 'gpay-link': element(), 'ios-payment-note': element(),
        'settlement-submit-amount': element(), 'settlement-display': element(),
        'settlement-copy-amount': element(),
    };
    const dialog = {
        dataset: {fullAmount: '100.00', upiId: upi, payeeName: 'Bank + Name & Co'},
        querySelector(selector) {
            if (selector.includes('type="radio"')) return mode;
            return fields[selector.slice(6, -1)];
        },
        querySelectorAll() { return [full, partial]; },
    };
    const copied = [];
    const context = {document: {
        querySelectorAll() { return [dialog]; }, querySelector() { return null; },
    }, window: {location: {href: 'https://tracker.test/groups/1/'}}, navigator: {userAgent, platform, maxTouchPoints: touches, clipboard: {async writeText(value) {
        if (clipboardFails) throw new Error('denied'); copied.push(value);
    }}}};
    vm.runInNewContext(source, context);
    return {fields, copied, form,
        partial(value) { mode = partial; fields['settlement-amount'].value = value; partial.listeners.change(); },
        full() { mode = full; full.listeners.change(); },
    };
}

test('full and partial payment use exact selected amount without an extra confirmation checkbox', async () => {
    const f = fixture();
    assert.equal(f.fields['settlement-submit-amount'].value, '100.00');
    f.partial('25.75');
    await f.fields['settlement-copy-amount'].listeners.click();
    assert.deepEqual(f.copied, ['25.75']);
    assert.equal(f.fields['settlement-submit-amount'].value, '25.75');
    f.full();
    assert.equal(f.fields['settlement-submit-amount'].value, '100.00');
});

test('invalid amounts prevent submitting a claim', () => {
    const f = fixture();
    for (const amount of ['0', '-1', '100.01', '1.001', 'NaN', '1e1', '']) {
        f.partial(amount);
        assert.equal(f.fields['settlement-submit-amount'].value, '');
        let prevented = false;
        f.form.listeners.submit({preventDefault() { prevented = true; }});
        assert.equal(prevented, true);
    }
});

test('denied clipboard leaves manual reporting usable', async () => {
    const f = fixture({clipboardFails: true});
    f.partial('7.50');
    await f.fields['settlement-copy-amount'].listeners.click();
    assert.match(f.fields['payment-copy-status'].textContent, /₹7.50/);
    f.form.listeners.submit({preventDefault() { throw new Error('valid manual report blocked'); }});
});


test('Android GPay intent encodes the recipient, name and selected amount; opening does not mark paid', () => {
    const f = fixture();
    f.partial('25.75');
    const link = f.fields['gpay-link'];
    assert.equal(link.hidden, false);
    assert.match(link.attrs.href, /^intent:\/\/pay\?/);
    const query = new URLSearchParams(link.attrs.href.split('?')[1].split('#')[0]);
    assert.equal(query.get('pa'), 'receiver@oksbi');
    assert.equal(query.get('pn'), 'Bank + Name & Co');
    assert.equal(query.get('am'), '25.75');
    assert.match(link.attrs.href, /package=com.google.android.apps.nbu.paisa.user/);
    link.listeners.click({preventDefault() { throw new Error('Valid launch blocked'); }});
});

test('iPhone and desktop-mode iPad show manual instructions and never a native link', () => {
    for (const device of [{userAgent:'iPhone'}, {userAgent:'Macintosh',platform:'MacIntel',touches:5}]) {
        const f = fixture(device);
        assert.equal(f.fields['gpay-link'].hidden, true);
        assert.equal(f.fields['gpay-link'].attrs.href, undefined);
        assert.equal(f.fields['ios-payment-note'].hidden, false);
    }
});

test('invalid UPI or amount cannot launch GPay', () => {
    for (const upi of ['', 'bad@bank&pa=other@bank']) {
        const f = fixture({upi});
        assert.equal(f.fields['gpay-link'].hidden, true);
        assert.equal(f.fields['gpay-link'].attrs.href, undefined);
    }
    const f = fixture(); f.partial('100.01');
    assert.equal(f.fields['gpay-link'].attrs.href, undefined);
});
