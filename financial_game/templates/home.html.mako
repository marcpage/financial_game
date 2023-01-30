<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>The Real-Life Financial Game</title>
        <style>
            <%include file="styles.css"/>
        </style>
        <script>
            <%include file="scripts.js"/>
        </script>
    </head>
    <body>
        <h1>The Real-Life Financial Game</h1>
        % if user is None:
            <%include file="login.html.mako"/>
        % else:
            <%include file="logout.html.mako"/>
            <%include file="add_account.html.mako"/>
        % endif
    </body>
</html>
