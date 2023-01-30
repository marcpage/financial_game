        <div class="login">
            % if message is not None:
                <p class="error">
                    ${message}
                </p>
            % endif
            <form method="POST" action="/login">
                <input name="email" type="email" autofocus placeholder="email" required size=20/>
                <input name="password" type="password" placeholder="password" required size=20 minlength=6/>
                <input type="submit" value="login"/>
            </form>
        </div>
