ALTER TABLE zemauth_user DROP CONSTRAINT zemauth_user_email_key;
CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user (lower(email));
                