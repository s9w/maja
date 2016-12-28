# dampy

## setup
StackExchange has limits imposed on the number of requests a program can make. To increase these limits, the program needs to be authenticated. The program does not use this authentification to access *any* user data. But there is no other way to authenticate without minimal access.

To authenticate, go to [https://stackexchange.com/oauth/dialog?client_id=8691&scope=no_expiry&redirect_uri=https://stackexchange.com/oauth/login_success](this) site and accept. You'll be redirected to another site. From its url, copy the string after `access_token=` into the `se_access_token` value in `secrets.json".`