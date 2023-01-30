        <div>
            <form method="POST" action="/add_account">
                <select name="bank" id="bank" required onchange="show_bank_account_type()">
                    <option value="" selected disabled>Bank</option>
                % for bank in sorted(banks, key=lambda b:b.name):
                    <option value=${bank.id}>${bank.name}</option>
                % endfor
                    <option value=-1>Other Bank …</option>
                </select>
                <br/>
                % for bank in banks:
                <div id="bank_${bank.id}" class="account_type">
                    <select id="bank_${bank.id}_account_type" name="bank_${bank.id}_account_type" set_required onchange="show_hide_other()">
                        <option value="" selected disabled>Product</option>
                    % for account_type in sorted(account_types[bank.id], key=lambda t:t.name):
                        <option value=${account_type.id}>${account_type.name}</option>
                    % endfor
                        <option value=-1>Other Product …</option>
                    </select>
                    <br/>
                </div>
                % endfor
                <div id="bank_-1" class="account_type">
                    <input name="bank_name" type="text" placeholder="Bank Name" set_required size=50/>
                    <input name="bank_url" type="text" placeholder="login URL (optional)" size=100/>
                    <br/>
                </div>
                <div id="account_type-1" class="new_account_type">
                    <select name="acount_type_category" set_required>
                        <option value="" selected disabled>Type</option>
                        <option value="CRED">Credit Card</option>
                        <option value="CHCK">Checking / Debit Card</option>
                        <option value="SAVE">Savings</option>
                        <option value="MONM">Money Market</option>
                        <option value="BROK">Brokerage</option>
                    </select>
                    <input name="account_type_name" type="text" placeholder="Product" set_required size=50/>
                    <input name="account_type_url" type="text" placeholder="login URL (optional)" size=100/>
                </div>
                <input name="account_label" type="text" placeholder="Label" required size=50/><br/>
                <input name="account_hint" type="text" placeholder="Login Hint (optional)" size=50/>
                <br/>
                <select name="account_purpose">
                    <option value="" selected>Purpose (optional)</option>
                    <option value="MRGC">Emergency Fund</option>
                    <option value="SINK">Targeted / Sinking Fund</option>
                    <option value="NYOU">Invest in Yourself Fund</option>
                    <option value="BUDG">Budget</option>
                    <option value="RTIR">Retirement</option>
                    <option value="NVST">Taxable Investments</option>
                </select>
                <br/>
                <input type="submit" value="add"/>
            </form>
        </div>
