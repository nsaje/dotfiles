--- Creates admin user 'dev@zemanta.com' with password 'admin'

COPY zemauth_user (id, password, last_login, is_superuser, email, username, first_name, last_name, date_joined, is_staff, is_active, is_test_user) FROM stdin;
1	pbkdf2_sha256$24000$GSWijssN2W0b$J0Hd1hjyMLM6BIn9xKPDSRlNU8IYx8QvqkcQPo+PI8Y=	2016-09-16 13:18:05.637437+00	t	dev@zemanta.com	\N			2016-09-16 13:18:05.637437+00	t	t	f
\.
SELECT pg_catalog.setval('zemauth_user_id_seq', 1, true);
