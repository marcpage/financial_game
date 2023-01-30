function change_visibility(div, show) {
    var inputs = Array.prototype.slice.call(div.getElementsByTagName("input"), 0);
    var selects = Array.prototype.slice.call(div.getElementsByTagName("select"), 0);

    inputs.concat(selects);
    div.style.display = show ? "block" : "none";

    for (var i=0; i < inputs.length; ++i) {
        if (inputs[i].hasAttribute('set_required')) {
            inputs[i].required = show;
        }
    }
}

function show_hide_other() {
    var bank = document.getElementById('bank');
    var display_new_account_type = bank.value == -1;
    var types = document.getElementsByClassName("new_account_type");

    if (!display_new_account_type) {
        var type = document.getElementById('bank_' + bank.value + '_account_type');

        display_new_account_type = type.value == -1;
    }

    for (var i=0; i < types.length; ++i) {
        change_visibility(types[i], display_new_account_type);
    }
}

function show_bank_account_type() {
    var bank = document.getElementById('bank');
    var type = document.getElementById('bank_' + bank.value);
    var types = document.getElementsByClassName("account_type");

    for (var i=0; i < types.length; ++i) {
        change_visibility(types[i], types[i] == type);
    }

    show_hide_other();
}
