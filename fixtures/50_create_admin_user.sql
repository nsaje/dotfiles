--- Creates admin user 'dev@zemanta.com' with password 'admin'

COPY zemauth_user (id, password, last_login, is_superuser, email, username, first_name, last_name, date_joined, is_staff, is_active, show_onboarding_guidance, is_test_user) FROM stdin;
1	pbkdf2_sha256$20000$lmycFWBC6IYf$k373ya5fBTbKDJ2d2qgETn8VGvQlqtC9xMEtQfbvMnA=	2015-10-07 11:18:28.722636+00	t	dev@zemanta.com				2015-10-07 11:18:28.722636+00	t	t	f	f
\.
SELECT pg_catalog.setval('zemauth_user_id_seq', 1, true);
