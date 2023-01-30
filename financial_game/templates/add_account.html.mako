        <div>
            <form method="POST" action="/add_account">
                <select name="bank" id="bank" required onchange="show_bank_account_type()">
                    <option value="" selected disabled>Bank</option>
                % for bank in banks:
                    <option value=${bank.id}>${bank.name}</option>
                % endfor
                    <option value=-1>Other …</option>
                </select>
                % for bank in banks:
                <div id="bank_${bank.id}" style="display:none">
                    <select name="bank_${bank.id}_account_type" required>
                        <option value="" selected disabled>Account Type</option>
                    % for account_type in account_types[${bank.id}]:
                        <option value=${account_type.id}>${account_type.name}</option>
                    % endfor
                        <option value=-1>Other …</option>
                    </select>
                </div>
                % endfor
                <div id="bank_-1" style="display:none">
                    <input name="bank_name" type="text" placeholder="Bank Name" required size=50/>
                    <input name="bank_url" type="text" placeholder="login URL" required size=100/>
                </div>
                <div id="account_type=-1" style="display:none">
                    <input name="account_type_name" type="text" placeholder="Account Type" required size=50/>
                    <input name="account_type_url" type="text" placeholder="login URL" required size=100/>
                    <select name="acount_type_category" required>
                        <option value="" selected disabled>Type</option>
                        <option value="CRED">Credit Card</option>
                        <option value="CHCK">Checking / Debit Card</option>
                        <option value="SAVE">Savings</option>
                        <option value="MONM">Money Market</option>
                        <option value="BROK">Brokerage</option>
                    </select>
                </div>
                <input name="account_label" type="text" placeholder="Account Label" required size=50/>
                <input name="account_hint" type="text" placeholder="Login Hint (optional)" required size=50/>
                <select name="account_purpose">
                    <option value="" selected>Purpose (optional)</option>
                    <option value="MRGC">Emergency Fund</option>
                    <option value="SINK">Targeted / Sinking Fund</option>
                    <option value="NYOU">Invest in Yourself Fund</option>
                    <option value="BUDG">Budget</option>
                    <option value="RTIR">Retirement</option>
                    <option value="NVST">Taxable Investments</option>
                </select>
                <input type="submit" value="add"/>
            </form>
        </div>
