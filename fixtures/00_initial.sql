--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: actionlog_actionlog; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE actionlog_actionlog (
    id integer NOT NULL,
    action character varying(100) NOT NULL,
    state integer NOT NULL,
    action_type integer NOT NULL,
    message text NOT NULL,
    payload text NOT NULL,
    expiration_dt timestamp with time zone,
    created_dt timestamp with time zone,
    modified_dt timestamp with time zone,
    ad_group_source_id integer,
    created_by_id integer,
    modified_by_id integer,
    order_id integer,
    content_ad_source_id integer
);


ALTER TABLE public.actionlog_actionlog OWNER TO eins;

--
-- Name: actionlog_actionlog_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE actionlog_actionlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.actionlog_actionlog_id_seq OWNER TO eins;

--
-- Name: actionlog_actionlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE actionlog_actionlog_id_seq OWNED BY actionlog_actionlog.id;


--
-- Name: actionlog_actionlogorder; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE actionlog_actionlogorder (
    id integer NOT NULL,
    order_type integer NOT NULL,
    created_dt timestamp with time zone
);


ALTER TABLE public.actionlog_actionlogorder OWNER TO eins;

--
-- Name: actionlog_actionlogorder_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE actionlog_actionlogorder_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.actionlog_actionlogorder_id_seq OWNER TO eins;

--
-- Name: actionlog_actionlogorder_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE actionlog_actionlogorder_id_seq OWNED BY actionlog_actionlogorder.id;


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE auth_group (
    id integer NOT NULL,
    name character varying(80) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO eins;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_id_seq OWNER TO eins;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE auth_group_id_seq OWNED BY auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO eins;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_permissions_id_seq OWNER TO eins;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE auth_group_permissions_id_seq OWNED BY auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO eins;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_permission_id_seq OWNER TO eins;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE auth_permission_id_seq OWNED BY auth_permission.id;


--
-- Name: automation_autopilotadgroupsourcebidcpclog; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE automation_autopilotadgroupsourcebidcpclog (
    id integer NOT NULL,
    created_dt timestamp with time zone,
    yesterdays_spend_cc numeric(10,4),
    previous_cpc_cc numeric(10,4),
    new_cpc_cc numeric(10,4),
    current_daily_budget_cc numeric(10,4),
    ad_group_id integer NOT NULL,
    ad_group_source_id integer NOT NULL,
    campaign_id integer NOT NULL,
    yesterdays_clicks integer,
    comments character varying(1024)
);


ALTER TABLE public.automation_autopilotadgroupsourcebidcpclog OWNER TO eins;

--
-- Name: automation_autopilotadgroupsourcebidcpclog_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE automation_autopilotadgroupsourcebidcpclog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.automation_autopilotadgroupsourcebidcpclog_id_seq OWNER TO eins;

--
-- Name: automation_autopilotadgroupsourcebidcpclog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE automation_autopilotadgroupsourcebidcpclog_id_seq OWNED BY automation_autopilotadgroupsourcebidcpclog.id;


--
-- Name: automation_campaignbudgetdepletionnotification; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE automation_campaignbudgetdepletionnotification (
    id integer NOT NULL,
    created_dt timestamp with time zone,
    available_budget numeric(20,4),
    yesterdays_spend numeric(20,4),
    account_manager_id integer,
    campaign_id integer NOT NULL,
    stopped boolean NOT NULL
);


ALTER TABLE public.automation_campaignbudgetdepletionnotification OWNER TO eins;

--
-- Name: automation_campaignbudgetdepletionnotification_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE automation_campaignbudgetdepletionnotification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.automation_campaignbudgetdepletionnotification_id_seq OWNER TO eins;

--
-- Name: automation_campaignbudgetdepletionnotification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE automation_campaignbudgetdepletionnotification_id_seq OWNED BY automation_campaignbudgetdepletionnotification.id;


--
-- Name: convapi_gareportlog; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE convapi_gareportlog (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    for_date date,
    email_subject character varying(1024),
    csv_filename character varying(1024),
    ad_groups character varying(128),
    visits_reported integer,
    visits_imported integer,
    state integer NOT NULL,
    errors text,
    multimatch integer NOT NULL,
    multimatch_clicks integer NOT NULL,
    nomatch integer NOT NULL,
    from_address character varying(1024),
    s3_key character varying(1024)
);


ALTER TABLE public.convapi_gareportlog OWNER TO eins;

--
-- Name: convapi_gareportlog_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE convapi_gareportlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.convapi_gareportlog_id_seq OWNER TO eins;

--
-- Name: convapi_gareportlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE convapi_gareportlog_id_seq OWNED BY convapi_gareportlog.id;


--
-- Name: convapi_rawgoalconversionstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE convapi_rawgoalconversionstats (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    source_id integer,
    url_raw character varying(2048) NOT NULL,
    url_clean character varying(2048) NOT NULL,
    device_type character varying(64),
    goal_name character varying(127) NOT NULL,
    z1_adgid character varying(32) NOT NULL,
    z1_msid character varying(64) NOT NULL,
    conversions integer NOT NULL,
    conversions_value_cc integer NOT NULL
);


ALTER TABLE public.convapi_rawgoalconversionstats OWNER TO eins;

--
-- Name: convapi_rawgoalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE convapi_rawgoalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.convapi_rawgoalconversionstats_id_seq OWNER TO eins;

--
-- Name: convapi_rawgoalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE convapi_rawgoalconversionstats_id_seq OWNED BY convapi_rawgoalconversionstats.id;


--
-- Name: convapi_rawpostclickstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE convapi_rawpostclickstats (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    source_id integer,
    url_raw character varying(2048) NOT NULL,
    url_clean character varying(2048) NOT NULL,
    device_type character varying(64),
    z1_adgid character varying(32) NOT NULL,
    z1_msid character varying(64) NOT NULL,
    visits integer NOT NULL,
    new_visits integer NOT NULL,
    bounced_visits integer NOT NULL,
    pageviews integer NOT NULL,
    duration integer NOT NULL
);


ALTER TABLE public.convapi_rawpostclickstats OWNER TO eins;

--
-- Name: convapi_rawpostclickstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE convapi_rawpostclickstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.convapi_rawpostclickstats_id_seq OWNER TO eins;

--
-- Name: convapi_rawpostclickstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE convapi_rawpostclickstats_id_seq OWNED BY convapi_rawpostclickstats.id;


--
-- Name: convapi_reportlog; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE convapi_reportlog (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    for_date date,
    email_subject character varying(1024),
    from_address character varying(1024),
    report_filename character varying(1024),
    visits_reported integer,
    visits_imported integer,
    state integer NOT NULL,
    errors text,
    s3_key character varying(1024)
);


ALTER TABLE public.convapi_reportlog OWNER TO eins;

--
-- Name: convapi_reportlog_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE convapi_reportlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.convapi_reportlog_id_seq OWNER TO eins;

--
-- Name: convapi_reportlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE convapi_reportlog_id_seq OWNED BY convapi_reportlog.id;


--
-- Name: dash_account; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_account (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    modified_by_id integer NOT NULL,
    outbrain_marketer_id character varying(255)
);


ALTER TABLE public.dash_account OWNER TO eins;

--
-- Name: dash_account_groups; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_account_groups (
    id integer NOT NULL,
    account_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.dash_account_groups OWNER TO eins;

--
-- Name: dash_account_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_account_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_account_groups_id_seq OWNER TO eins;

--
-- Name: dash_account_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_account_groups_id_seq OWNED BY dash_account_groups.id;


--
-- Name: dash_account_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_account_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_account_id_seq OWNER TO eins;

--
-- Name: dash_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_account_id_seq OWNED BY dash_account.id;


--
-- Name: dash_account_users; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_account_users (
    id integer NOT NULL,
    account_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.dash_account_users OWNER TO eins;

--
-- Name: dash_account_users_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_account_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_account_users_id_seq OWNER TO eins;

--
-- Name: dash_account_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_account_users_id_seq OWNED BY dash_account_users.id;


--
-- Name: dash_accountsettings; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_accountsettings (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    archived boolean NOT NULL,
    account_id integer NOT NULL,
    created_by_id integer NOT NULL,
    changes_text text,
    default_account_manager_id integer,
    default_sales_representative_id integer,
    service_fee numeric(5,4) NOT NULL
);


ALTER TABLE public.dash_accountsettings OWNER TO eins;

--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_accountsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_accountsettings_id_seq OWNER TO eins;

--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_accountsettings_id_seq OWNED BY dash_accountsettings.id;


--
-- Name: dash_adgroup; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_adgroup (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    modified_by_id integer NOT NULL,
    campaign_id integer NOT NULL,
    is_demo boolean NOT NULL,
    content_ads_tab_with_cms boolean NOT NULL
);


ALTER TABLE public.dash_adgroup OWNER TO eins;

--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_adgroup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_adgroup_id_seq OWNER TO eins;

--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_adgroup_id_seq OWNED BY dash_adgroup.id;


--
-- Name: dash_adgroupsettings; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_adgroupsettings (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    start_date date,
    end_date date,
    cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    target_devices text NOT NULL,
    target_regions text NOT NULL,
    tracking_code text NOT NULL,
    ad_group_id integer NOT NULL,
    created_by_id integer,
    archived boolean NOT NULL,
    changes_text text,
    brand_name character varying(25) NOT NULL,
    call_to_action character varying(25) NOT NULL,
    description character varying(140) NOT NULL,
    display_url character varying(25) NOT NULL,
    ad_group_name character varying(127) NOT NULL,
    enable_ga_tracking boolean NOT NULL,
    adobe_tracking_param character varying(10) NOT NULL,
    enable_adobe_tracking boolean NOT NULL
);


ALTER TABLE public.dash_adgroupsettings OWNER TO eins;

--
-- Name: dash_adgroupsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_adgroupsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_adgroupsettings_id_seq OWNER TO eins;

--
-- Name: dash_adgroupsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_adgroupsettings_id_seq OWNED BY dash_adgroupsettings.id;


--
-- Name: dash_adgroupsource; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_adgroupsource (
    id integer NOT NULL,
    source_campaign_key text NOT NULL,
    ad_group_id integer NOT NULL,
    source_id integer NOT NULL,
    source_credentials_id integer,
    last_successful_sync_dt timestamp with time zone,
    can_manage_content_ads boolean NOT NULL,
    source_content_ad_id character varying(100),
    submission_errors text,
    submission_status integer NOT NULL,
    last_successful_reports_sync_dt timestamp with time zone,
    last_successful_status_sync_dt timestamp with time zone
);


ALTER TABLE public.dash_adgroupsource OWNER TO eins;

--
-- Name: dash_adgroupsource_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_adgroupsource_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_adgroupsource_id_seq OWNER TO eins;

--
-- Name: dash_adgroupsource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_adgroupsource_id_seq OWNED BY dash_adgroupsource.id;


--
-- Name: dash_adgroupsourcesettings; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_adgroupsourcesettings (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    ad_group_source_id integer,
    created_by_id integer,
    autopilot_state integer NOT NULL
);


ALTER TABLE public.dash_adgroupsourcesettings OWNER TO eins;

--
-- Name: dash_adgroupsourcesettings_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_adgroupsourcesettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_adgroupsourcesettings_id_seq OWNER TO eins;

--
-- Name: dash_adgroupsourcesettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_adgroupsourcesettings_id_seq OWNED BY dash_adgroupsourcesettings.id;


--
-- Name: dash_adgroupsourcestate; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_adgroupsourcestate (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    ad_group_source_id integer
);


ALTER TABLE public.dash_adgroupsourcestate OWNER TO eins;

--
-- Name: dash_adgroupsourcestate_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_adgroupsourcestate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_adgroupsourcestate_id_seq OWNER TO eins;

--
-- Name: dash_adgroupsourcestate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_adgroupsourcestate_id_seq OWNED BY dash_adgroupsourcestate.id;


--
-- Name: dash_article; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_article (
    id integer NOT NULL,
    url character varying(2048) NOT NULL,
    title character varying(256) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL
);


ALTER TABLE public.dash_article OWNER TO eins;

--
-- Name: dash_article_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_article_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_article_id_seq OWNER TO eins;

--
-- Name: dash_article_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_article_id_seq OWNED BY dash_article.id;


--
-- Name: dash_budgethistory; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_budgethistory (
    id integer NOT NULL,
    snapshot text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    budget_id integer NOT NULL,
    created_by_id integer
);


ALTER TABLE public.dash_budgethistory OWNER TO eins;

--
-- Name: dash_budgethistory_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_budgethistory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_budgethistory_id_seq OWNER TO eins;

--
-- Name: dash_budgethistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_budgethistory_id_seq OWNED BY dash_budgethistory.id;


--
-- Name: dash_budgetlineitem; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_budgetlineitem (
    id integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    amount integer NOT NULL,
    comment character varying(256),
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    campaign_id integer NOT NULL,
    created_by_id integer,
    credit_id integer NOT NULL
);


ALTER TABLE public.dash_budgetlineitem OWNER TO eins;

--
-- Name: dash_budgetlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_budgetlineitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_budgetlineitem_id_seq OWNER TO eins;

--
-- Name: dash_budgetlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_budgetlineitem_id_seq OWNED BY dash_budgetlineitem.id;


--
-- Name: dash_campaign; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_campaign (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    account_id integer NOT NULL,
    modified_by_id integer NOT NULL
);


ALTER TABLE public.dash_campaign OWNER TO eins;

--
-- Name: dash_campaign_groups; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_campaign_groups (
    id integer NOT NULL,
    campaign_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.dash_campaign_groups OWNER TO eins;

--
-- Name: dash_campaign_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_campaign_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_campaign_groups_id_seq OWNER TO eins;

--
-- Name: dash_campaign_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_campaign_groups_id_seq OWNED BY dash_campaign_groups.id;


--
-- Name: dash_campaign_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_campaign_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_campaign_id_seq OWNER TO eins;

--
-- Name: dash_campaign_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_campaign_id_seq OWNED BY dash_campaign.id;


--
-- Name: dash_campaign_users; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_campaign_users (
    id integer NOT NULL,
    campaign_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.dash_campaign_users OWNER TO eins;

--
-- Name: dash_campaign_users_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_campaign_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_campaign_users_id_seq OWNER TO eins;

--
-- Name: dash_campaign_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_campaign_users_id_seq OWNED BY dash_campaign_users.id;


--
-- Name: dash_campaignbudgetsettings; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_campaignbudgetsettings (
    id integer NOT NULL,
    allocate numeric(20,4) NOT NULL,
    revoke numeric(20,4) NOT NULL,
    total numeric(20,4) NOT NULL,
    comment character varying(256) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    campaign_id integer NOT NULL,
    created_by_id integer NOT NULL
);


ALTER TABLE public.dash_campaignbudgetsettings OWNER TO eins;

--
-- Name: dash_campaignbudgetsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_campaignbudgetsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_campaignbudgetsettings_id_seq OWNER TO eins;

--
-- Name: dash_campaignbudgetsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_campaignbudgetsettings_id_seq OWNED BY dash_campaignbudgetsettings.id;


--
-- Name: dash_campaignsettings; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_campaignsettings (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    service_fee numeric(5,4) NOT NULL,
    iab_category character varying(10) NOT NULL,
    promotion_goal integer NOT NULL,
    account_manager_id integer,
    campaign_id integer NOT NULL,
    created_by_id integer NOT NULL,
    sales_representative_id integer,
    name character varying(127) NOT NULL,
    archived boolean NOT NULL,
    campaign_goal integer NOT NULL,
    goal_quantity numeric(20,2) NOT NULL,
    changes_text text
);


ALTER TABLE public.dash_campaignsettings OWNER TO eins;

--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_campaignsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_campaignsettings_id_seq OWNER TO eins;

--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_campaignsettings_id_seq OWNED BY dash_campaignsettings.id;


--
-- Name: dash_contentad; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_contentad (
    id integer NOT NULL,
    image_id character varying(256),
    batch_id integer NOT NULL,
    image_height integer,
    image_width integer,
    ad_group_id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    title character varying(256) NOT NULL,
    url character varying(2048) NOT NULL,
    image_hash character varying(128),
    state integer,
    redirect_id character varying(128),
    archived boolean NOT NULL,
    tracker_urls character varying(2048)[],
    brand_name character varying(25) NOT NULL,
    call_to_action character varying(25) NOT NULL,
    description character varying(140) NOT NULL,
    display_url character varying(25) NOT NULL,
    crop_areas character varying(128),
    CONSTRAINT dash_contentad_image_height_check CHECK ((image_height >= 0)),
    CONSTRAINT dash_contentad_image_width_check CHECK ((image_width >= 0))
);


ALTER TABLE public.dash_contentad OWNER TO eins;

--
-- Name: dash_contentad_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_contentad_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_contentad_id_seq OWNER TO eins;

--
-- Name: dash_contentad_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_contentad_id_seq OWNED BY dash_contentad.id;


--
-- Name: dash_contentadsource; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_contentadsource (
    id integer NOT NULL,
    submission_status integer NOT NULL,
    state integer,
    source_state integer,
    source_content_ad_id character varying(50),
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    content_ad_id integer NOT NULL,
    source_id integer NOT NULL,
    submission_errors text
);


ALTER TABLE public.dash_contentadsource OWNER TO eins;

--
-- Name: dash_contentadsource_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_contentadsource_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_contentadsource_id_seq OWNER TO eins;

--
-- Name: dash_contentadsource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_contentadsource_id_seq OWNED BY dash_contentadsource.id;


--
-- Name: dash_conversiongoal; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_conversiongoal (
    id integer NOT NULL,
    type smallint NOT NULL,
    name character varying(100) NOT NULL,
    conversion_window smallint,
    goal_id character varying(100),
    created_dt timestamp with time zone NOT NULL,
    campaign_id integer NOT NULL,
    pixel_id integer,
    CONSTRAINT dash_conversiongoal_conversion_window_check CHECK ((conversion_window >= 0)),
    CONSTRAINT dash_conversiongoal_type_check CHECK ((type >= 0))
);


ALTER TABLE public.dash_conversiongoal OWNER TO eins;

--
-- Name: dash_conversiongoal_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_conversiongoal_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_conversiongoal_id_seq OWNER TO eins;

--
-- Name: dash_conversiongoal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_conversiongoal_id_seq OWNED BY dash_conversiongoal.id;


--
-- Name: dash_conversionpixel; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_conversionpixel (
    id integer NOT NULL,
    slug character varying(32) NOT NULL,
    archived boolean NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    account_id integer NOT NULL,
    last_sync_dt timestamp with time zone
);


ALTER TABLE public.dash_conversionpixel OWNER TO eins;

--
-- Name: dash_conversionpixel_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_conversionpixel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_conversionpixel_id_seq OWNER TO eins;

--
-- Name: dash_conversionpixel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_conversionpixel_id_seq OWNED BY dash_conversionpixel.id;


--
-- Name: dash_credithistory; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_credithistory (
    id integer NOT NULL,
    snapshot text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    created_by_id integer,
    credit_id integer NOT NULL
);


ALTER TABLE public.dash_credithistory OWNER TO eins;

--
-- Name: dash_credithistory_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_credithistory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_credithistory_id_seq OWNER TO eins;

--
-- Name: dash_credithistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_credithistory_id_seq OWNED BY dash_credithistory.id;


--
-- Name: dash_creditlineitem; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_creditlineitem (
    id integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    amount integer NOT NULL,
    license_fee numeric(5,4) NOT NULL,
    status integer NOT NULL,
    comment character varying(256),
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    account_id integer NOT NULL,
    created_by_id integer
);


ALTER TABLE public.dash_creditlineitem OWNER TO eins;

--
-- Name: dash_creditlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_creditlineitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_creditlineitem_id_seq OWNER TO eins;

--
-- Name: dash_creditlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_creditlineitem_id_seq OWNED BY dash_creditlineitem.id;


--
-- Name: dash_defaultsourcesettings; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_defaultsourcesettings (
    id integer NOT NULL,
    credentials_id integer,
    source_id integer NOT NULL,
    params text NOT NULL,
    auto_add boolean NOT NULL,
    daily_budget_cc numeric(10,4),
    default_cpc_cc numeric(10,4),
    mobile_cpc_cc numeric(10,4)
);


ALTER TABLE public.dash_defaultsourcesettings OWNER TO eins;

--
-- Name: dash_defaultsourcesettings_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_defaultsourcesettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_defaultsourcesettings_id_seq OWNER TO eins;

--
-- Name: dash_defaultsourcesettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_defaultsourcesettings_id_seq OWNED BY dash_defaultsourcesettings.id;


--
-- Name: dash_demoadgrouprealadgroup; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_demoadgrouprealadgroup (
    id integer NOT NULL,
    multiplication_factor integer NOT NULL,
    demo_ad_group_id integer NOT NULL,
    real_ad_group_id integer NOT NULL
);


ALTER TABLE public.dash_demoadgrouprealadgroup OWNER TO eins;

--
-- Name: dash_demoadgrouprealadgroup_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_demoadgrouprealadgroup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_demoadgrouprealadgroup_id_seq OWNER TO eins;

--
-- Name: dash_demoadgrouprealadgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_demoadgrouprealadgroup_id_seq OWNED BY dash_demoadgrouprealadgroup.id;


--
-- Name: dash_exportreport; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_exportreport (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    granularity integer NOT NULL,
    breakdown_by_day boolean NOT NULL,
    breakdown_by_source boolean NOT NULL,
    order_by character varying(20),
    additional_fields character varying(500),
    account_id integer,
    ad_group_id integer,
    campaign_id integer,
    created_by_id integer NOT NULL
);


ALTER TABLE public.dash_exportreport OWNER TO eins;

--
-- Name: dash_exportreport_filtered_sources; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_exportreport_filtered_sources (
    id integer NOT NULL,
    exportreport_id integer NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.dash_exportreport_filtered_sources OWNER TO eins;

--
-- Name: dash_exportreport_filtered_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_exportreport_filtered_sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_exportreport_filtered_sources_id_seq OWNER TO eins;

--
-- Name: dash_exportreport_filtered_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_exportreport_filtered_sources_id_seq OWNED BY dash_exportreport_filtered_sources.id;


--
-- Name: dash_exportreport_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_exportreport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_exportreport_id_seq OWNER TO eins;

--
-- Name: dash_exportreport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_exportreport_id_seq OWNED BY dash_exportreport.id;


--
-- Name: dash_outbrainaccount; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_outbrainaccount (
    id integer NOT NULL,
    marketer_id character varying(255) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    used boolean NOT NULL
);


ALTER TABLE public.dash_outbrainaccount OWNER TO eins;

--
-- Name: dash_outbrainaccount_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_outbrainaccount_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_outbrainaccount_id_seq OWNER TO eins;

--
-- Name: dash_outbrainaccount_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_outbrainaccount_id_seq OWNED BY dash_outbrainaccount.id;


--
-- Name: dash_publisherblacklist; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_publisherblacklist (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    ad_group_id integer,
    source_id integer NOT NULL,
    status integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    account_id integer,
    campaign_id integer,
    everywhere boolean NOT NULL
);


ALTER TABLE public.dash_publisherblacklist OWNER TO eins;

--
-- Name: dash_publisherblacklist_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_publisherblacklist_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_publisherblacklist_id_seq OWNER TO eins;

--
-- Name: dash_publisherblacklist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_publisherblacklist_id_seq OWNED BY dash_publisherblacklist.id;


--
-- Name: dash_scheduledexportreport; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_scheduledexportreport (
    id integer NOT NULL,
    name character varying(100),
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    sending_frequency integer NOT NULL,
    created_by_id integer NOT NULL,
    report_id integer NOT NULL
);


ALTER TABLE public.dash_scheduledexportreport OWNER TO eins;

--
-- Name: dash_scheduledexportreport_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_scheduledexportreport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_scheduledexportreport_id_seq OWNER TO eins;

--
-- Name: dash_scheduledexportreport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_scheduledexportreport_id_seq OWNED BY dash_scheduledexportreport.id;


--
-- Name: dash_scheduledexportreportrecipient; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_scheduledexportreportrecipient (
    id integer NOT NULL,
    email character varying(254) NOT NULL,
    scheduled_report_id integer NOT NULL
);


ALTER TABLE public.dash_scheduledexportreportrecipient OWNER TO eins;

--
-- Name: dash_scheduledexportreportrecipient_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_scheduledexportreportrecipient_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_scheduledexportreportrecipient_id_seq OWNER TO eins;

--
-- Name: dash_scheduledexportreportrecipient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_scheduledexportreportrecipient_id_seq OWNED BY dash_scheduledexportreportrecipient.id;


--
-- Name: dash_source; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_source (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    maintenance boolean NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    source_type_id integer,
    tracking_slug character varying(50) NOT NULL,
    bidder_slug character varying(50),
    deprecated boolean NOT NULL,
    content_ad_submission_type integer NOT NULL
);


ALTER TABLE public.dash_source OWNER TO eins;

--
-- Name: dash_source_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_source_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_source_id_seq OWNER TO eins;

--
-- Name: dash_source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_source_id_seq OWNED BY dash_source.id;


--
-- Name: dash_sourcecredentials; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_sourcecredentials (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    credentials text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.dash_sourcecredentials OWNER TO eins;

--
-- Name: dash_sourcecredentials_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_sourcecredentials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_sourcecredentials_id_seq OWNER TO eins;

--
-- Name: dash_sourcecredentials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_sourcecredentials_id_seq OWNED BY dash_sourcecredentials.id;


--
-- Name: dash_sourcetype; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_sourcetype (
    id integer NOT NULL,
    type character varying(127) NOT NULL,
    min_cpc numeric(10,4),
    min_daily_budget numeric(10,4),
    max_cpc numeric(10,4),
    max_daily_budget numeric(10,4),
    cpc_decimal_places smallint,
    delete_traffic_metrics_threshold integer NOT NULL,
    available_actions smallint[],
    CONSTRAINT dash_sourcetype_cpc_decimal_places_check CHECK ((cpc_decimal_places >= 0))
);


ALTER TABLE public.dash_sourcetype OWNER TO eins;

--
-- Name: dash_sourcetype_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_sourcetype_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_sourcetype_id_seq OWNER TO eins;

--
-- Name: dash_sourcetype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_sourcetype_id_seq OWNED BY dash_sourcetype.id;


--
-- Name: dash_uploadbatch; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_uploadbatch (
    id integer NOT NULL,
    name character varying(1024) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    status integer NOT NULL,
    error_report_key character varying(1024),
    num_errors integer,
    batch_size integer,
    processed_content_ads integer,
    inserted_content_ads integer,
    CONSTRAINT dash_uploadbatch_batch_size_check CHECK ((batch_size >= 0)),
    CONSTRAINT dash_uploadbatch_inserted_content_ads_check CHECK ((inserted_content_ads >= 0)),
    CONSTRAINT dash_uploadbatch_num_errors_check CHECK ((num_errors >= 0)),
    CONSTRAINT dash_uploadbatch_processed_content_ads_check CHECK ((processed_content_ads >= 0))
);


ALTER TABLE public.dash_uploadbatch OWNER TO eins;

--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_uploadbatch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_uploadbatch_id_seq OWNER TO eins;

--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_uploadbatch_id_seq OWNED BY dash_uploadbatch.id;


--
-- Name: dash_useractionlog; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE dash_useractionlog (
    id integer NOT NULL,
    action_type smallint NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    account_id integer,
    account_settings_id integer,
    ad_group_id integer,
    ad_group_settings_id integer,
    campaign_id integer,
    campaign_settings_id integer,
    created_by_id integer,
    CONSTRAINT dash_useractionlog_action_type_check CHECK ((action_type >= 0))
);


ALTER TABLE public.dash_useractionlog OWNER TO eins;

--
-- Name: dash_useractionlog_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE dash_useractionlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dash_useractionlog_id_seq OWNER TO eins;

--
-- Name: dash_useractionlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE dash_useractionlog_id_seq OWNED BY dash_useractionlog.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO eins;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_admin_log_id_seq OWNER TO eins;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE django_admin_log_id_seq OWNED BY django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO eins;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_content_type_id_seq OWNER TO eins;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO eins;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_migrations_id_seq OWNER TO eins;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE django_migrations_id_seq OWNED BY django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO eins;

--
-- Name: reports_adgroupgoalconversionstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_adgroupgoalconversionstats (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    goal_name character varying(127) NOT NULL,
    conversions integer NOT NULL,
    conversions_value_cc integer NOT NULL,
    ad_group_id integer NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.reports_adgroupgoalconversionstats OWNER TO eins;

--
-- Name: reports_adgroupgoalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_adgroupgoalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_adgroupgoalconversionstats_id_seq OWNER TO eins;

--
-- Name: reports_adgroupgoalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_adgroupgoalconversionstats_id_seq OWNED BY reports_adgroupgoalconversionstats.id;


--
-- Name: reports_adgroupstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_adgroupstats (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    impressions integer NOT NULL,
    clicks integer NOT NULL,
    cost_cc integer NOT NULL,
    visits integer NOT NULL,
    new_visits integer NOT NULL,
    bounced_visits integer NOT NULL,
    pageviews integer NOT NULL,
    duration integer NOT NULL,
    has_traffic_metrics integer NOT NULL,
    has_postclick_metrics integer NOT NULL,
    has_conversion_metrics integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    source_id integer NOT NULL,
    data_cost_cc integer NOT NULL
);


ALTER TABLE public.reports_adgroupstats OWNER TO eins;

--
-- Name: reports_adgroupstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_adgroupstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_adgroupstats_id_seq OWNER TO eins;

--
-- Name: reports_adgroupstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_adgroupstats_id_seq OWNED BY reports_adgroupstats.id;


--
-- Name: reports_articlestats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_articlestats (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    impressions integer NOT NULL,
    clicks integer NOT NULL,
    cost_cc integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    article_id integer NOT NULL,
    source_id integer NOT NULL,
    bounced_visits integer NOT NULL,
    duration integer NOT NULL,
    has_postclick_metrics integer NOT NULL,
    has_traffic_metrics integer NOT NULL,
    new_visits integer NOT NULL,
    pageviews integer NOT NULL,
    visits integer NOT NULL,
    has_conversion_metrics integer NOT NULL,
    data_cost_cc integer NOT NULL
);


ALTER TABLE public.reports_articlestats OWNER TO eins;

--
-- Name: reports_articlestats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_articlestats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_articlestats_id_seq OWNER TO eins;

--
-- Name: reports_articlestats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_articlestats_id_seq OWNED BY reports_articlestats.id;


--
-- Name: reports_contentadgoalconversionstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_contentadgoalconversionstats (
    id integer NOT NULL,
    date timestamp with time zone NOT NULL,
    goal_type character varying(15) NOT NULL,
    goal_name character varying(256) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    content_ad_id integer NOT NULL,
    source_id integer NOT NULL,
    conversions integer
);


ALTER TABLE public.reports_contentadgoalconversionstats OWNER TO eins;

--
-- Name: reports_contentadgoalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_contentadgoalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_contentadgoalconversionstats_id_seq OWNER TO eins;

--
-- Name: reports_contentadgoalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_contentadgoalconversionstats_id_seq OWNED BY reports_contentadgoalconversionstats.id;


--
-- Name: reports_contentadpostclickstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_contentadpostclickstats (
    id integer NOT NULL,
    date date NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    visits integer,
    new_visits integer,
    bounced_visits integer,
    pageviews integer,
    total_time_on_site integer,
    content_ad_id integer NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.reports_contentadpostclickstats OWNER TO eins;

--
-- Name: reports_contentadpostclickstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_contentadpostclickstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_contentadpostclickstats_id_seq OWNER TO eins;

--
-- Name: reports_contentadpostclickstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_contentadpostclickstats_id_seq OWNED BY reports_contentadpostclickstats.id;


--
-- Name: reports_contentadstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_contentadstats (
    id integer NOT NULL,
    impressions integer,
    clicks integer,
    cost_cc integer,
    data_cost_cc integer,
    date date NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    content_ad_id integer NOT NULL,
    content_ad_source_id integer NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.reports_contentadstats OWNER TO eins;

--
-- Name: reports_contentadstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_contentadstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_contentadstats_id_seq OWNER TO eins;

--
-- Name: reports_contentadstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_contentadstats_id_seq OWNED BY reports_contentadstats.id;


--
-- Name: reports_goalconversionstats; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_goalconversionstats (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    goal_name character varying(127) NOT NULL,
    conversions integer NOT NULL,
    conversions_value_cc integer NOT NULL,
    ad_group_id integer NOT NULL,
    article_id integer NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.reports_goalconversionstats OWNER TO eins;

--
-- Name: reports_goalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_goalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_goalconversionstats_id_seq OWNER TO eins;

--
-- Name: reports_goalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_goalconversionstats_id_seq OWNED BY reports_goalconversionstats.id;


--
-- Name: reports_supplyreportrecipient; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE reports_supplyreportrecipient (
    id integer NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    email character varying(255) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    source_id integer NOT NULL
);


ALTER TABLE public.reports_supplyreportrecipient OWNER TO eins;

--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE reports_supplyreportrecipient_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reports_supplyreportrecipient_id_seq OWNER TO eins;

--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE reports_supplyreportrecipient_id_seq OWNED BY reports_supplyreportrecipient.id;


--
-- Name: zemauth_internalgroup; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE zemauth_internalgroup (
    id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.zemauth_internalgroup OWNER TO eins;

--
-- Name: zemauth_internalgroup_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE zemauth_internalgroup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.zemauth_internalgroup_id_seq OWNER TO eins;

--
-- Name: zemauth_internalgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE zemauth_internalgroup_id_seq OWNED BY zemauth_internalgroup.id;


--
-- Name: zemauth_user; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE zemauth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(30) NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    show_onboarding_guidance boolean NOT NULL
);


ALTER TABLE public.zemauth_user OWNER TO eins;

--
-- Name: zemauth_user_groups; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE zemauth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.zemauth_user_groups OWNER TO eins;

--
-- Name: zemauth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE zemauth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.zemauth_user_groups_id_seq OWNER TO eins;

--
-- Name: zemauth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE zemauth_user_groups_id_seq OWNED BY zemauth_user_groups.id;


--
-- Name: zemauth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE zemauth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.zemauth_user_id_seq OWNER TO eins;

--
-- Name: zemauth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE zemauth_user_id_seq OWNED BY zemauth_user.id;


--
-- Name: zemauth_user_user_permissions; Type: TABLE; Schema: public; Owner: eins; Tablespace:
--

CREATE TABLE zemauth_user_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.zemauth_user_user_permissions OWNER TO eins;

--
-- Name: zemauth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: eins
--

CREATE SEQUENCE zemauth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.zemauth_user_user_permissions_id_seq OWNER TO eins;

--
-- Name: zemauth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eins
--

ALTER SEQUENCE zemauth_user_user_permissions_id_seq OWNED BY zemauth_user_user_permissions.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlog ALTER COLUMN id SET DEFAULT nextval('actionlog_actionlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlogorder ALTER COLUMN id SET DEFAULT nextval('actionlog_actionlogorder_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY auth_group ALTER COLUMN id SET DEFAULT nextval('auth_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('auth_group_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog ALTER COLUMN id SET DEFAULT nextval('automation_autopilotadgroupsourcebidcpclog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification ALTER COLUMN id SET DEFAULT nextval('automation_campaignbudgetdepletionnotification_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY convapi_gareportlog ALTER COLUMN id SET DEFAULT nextval('convapi_gareportlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY convapi_rawgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('convapi_rawgoalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY convapi_rawpostclickstats ALTER COLUMN id SET DEFAULT nextval('convapi_rawpostclickstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY convapi_reportlog ALTER COLUMN id SET DEFAULT nextval('convapi_reportlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account ALTER COLUMN id SET DEFAULT nextval('dash_account_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account_groups ALTER COLUMN id SET DEFAULT nextval('dash_account_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account_users ALTER COLUMN id SET DEFAULT nextval('dash_account_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_accountsettings ALTER COLUMN id SET DEFAULT nextval('dash_accountsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroup ALTER COLUMN id SET DEFAULT nextval('dash_adgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsettings ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsource ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsource_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsourcesettings ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsourcesettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsourcestate ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsourcestate_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_article ALTER COLUMN id SET DEFAULT nextval('dash_article_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgethistory ALTER COLUMN id SET DEFAULT nextval('dash_budgethistory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgetlineitem ALTER COLUMN id SET DEFAULT nextval('dash_budgetlineitem_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign ALTER COLUMN id SET DEFAULT nextval('dash_campaign_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign_groups ALTER COLUMN id SET DEFAULT nextval('dash_campaign_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign_users ALTER COLUMN id SET DEFAULT nextval('dash_campaign_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignbudgetsettings ALTER COLUMN id SET DEFAULT nextval('dash_campaignbudgetsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignsettings ALTER COLUMN id SET DEFAULT nextval('dash_campaignsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_contentad ALTER COLUMN id SET DEFAULT nextval('dash_contentad_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_contentadsource ALTER COLUMN id SET DEFAULT nextval('dash_contentadsource_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_conversiongoal ALTER COLUMN id SET DEFAULT nextval('dash_conversiongoal_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_conversionpixel ALTER COLUMN id SET DEFAULT nextval('dash_conversionpixel_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_credithistory ALTER COLUMN id SET DEFAULT nextval('dash_credithistory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_creditlineitem ALTER COLUMN id SET DEFAULT nextval('dash_creditlineitem_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_defaultsourcesettings ALTER COLUMN id SET DEFAULT nextval('dash_defaultsourcesettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup ALTER COLUMN id SET DEFAULT nextval('dash_demoadgrouprealadgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport_filtered_sources ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_filtered_sources_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_outbrainaccount ALTER COLUMN id SET DEFAULT nextval('dash_outbrainaccount_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_publisherblacklist ALTER COLUMN id SET DEFAULT nextval('dash_publisherblacklist_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_scheduledexportreport ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreport_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreportrecipient_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_source ALTER COLUMN id SET DEFAULT nextval('dash_source_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_sourcecredentials ALTER COLUMN id SET DEFAULT nextval('dash_sourcecredentials_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_sourcetype ALTER COLUMN id SET DEFAULT nextval('dash_sourcetype_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_uploadbatch ALTER COLUMN id SET DEFAULT nextval('dash_uploadbatch_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog ALTER COLUMN id SET DEFAULT nextval('dash_useractionlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_adgroupgoalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_adgroupstats ALTER COLUMN id SET DEFAULT nextval('reports_adgroupstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_articlestats ALTER COLUMN id SET DEFAULT nextval('reports_articlestats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadgoalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadpostclickstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadpostclickstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_goalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_goalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_supplyreportrecipient ALTER COLUMN id SET DEFAULT nextval('reports_supplyreportrecipient_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_internalgroup ALTER COLUMN id SET DEFAULT nextval('zemauth_internalgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user ALTER COLUMN id SET DEFAULT nextval('zemauth_user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user_groups ALTER COLUMN id SET DEFAULT nextval('zemauth_user_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('zemauth_user_user_permissions_id_seq'::regclass);


--
-- Data for Name: actionlog_actionlog; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY actionlog_actionlog (id, action, state, action_type, message, payload, expiration_dt, created_dt, modified_dt, ad_group_source_id, created_by_id, modified_by_id, order_id, content_ad_source_id) FROM stdin;
\.


--
-- Name: actionlog_actionlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('actionlog_actionlog_id_seq', 1, false);


--
-- Data for Name: actionlog_actionlogorder; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY actionlog_actionlogorder (id, order_type, created_dt) FROM stdin;
\.


--
-- Name: actionlog_actionlogorder_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('actionlog_actionlogorder_id_seq', 1, false);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY auth_group (id, name) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('auth_group_id_seq', 1, false);


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', 1, false);


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can add permission	2	add_permission
5	Can change permission	2	change_permission
6	Can delete permission	2	delete_permission
7	Can add group	3	add_group
8	Can change group	3	change_group
9	Can delete group	3	delete_group
10	Can add content type	4	add_contenttype
11	Can change content type	4	change_contenttype
12	Can delete content type	4	delete_contenttype
13	Can add session	5	add_session
14	Can change session	5	change_session
15	Can delete session	5	delete_session
16	Can add outbrain account	6	add_outbrainaccount
17	Can change outbrain account	6	change_outbrainaccount
18	Can delete outbrain account	6	delete_outbrainaccount
19	Can add account	7	add_account
20	Can change account	7	change_account
21	Can delete account	7	delete_account
22	All new accounts are automatically added to group.	7	group_account_automatically_add
23	Can add campaign	8	add_campaign
24	Can change campaign	8	change_campaign
25	Can delete campaign	8	delete_campaign
26	Can add account settings	9	add_accountsettings
27	Can change account settings	9	change_accountsettings
28	Can delete account settings	9	delete_accountsettings
29	Can add campaign settings	10	add_campaignsettings
30	Can change campaign settings	10	change_campaignsettings
31	Can delete campaign settings	10	delete_campaignsettings
32	Can add Source Type	11	add_sourcetype
33	Can change Source Type	11	change_sourcetype
34	Can delete Source Type	11	delete_sourcetype
35	Can add source	12	add_source
36	Can change source	12	change_source
37	Can delete source	12	delete_source
38	Can add source credentials	13	add_sourcecredentials
39	Can change source credentials	13	change_sourcecredentials
40	Can delete source credentials	13	delete_sourcecredentials
41	Can add default source settings	14	add_defaultsourcesettings
42	Can change default source settings	14	change_defaultsourcesettings
43	Can delete default source settings	14	delete_defaultsourcesettings
44	Can add ad group	15	add_adgroup
45	Can change ad group	15	change_adgroup
46	Can delete ad group	15	delete_adgroup
47	Can add ad group source	16	add_adgroupsource
48	Can change ad group source	16	change_adgroupsource
49	Can delete ad group source	16	delete_adgroupsource
50	Can add ad group settings	17	add_adgroupsettings
51	Can change ad group settings	17	change_adgroupsettings
52	Can delete ad group settings	17	delete_adgroupsettings
53	Can view settings in dashboard.	17	settings_view
54	Can add ad group source state	18	add_adgroupsourcestate
55	Can change ad group source state	18	change_adgroupsourcestate
56	Can delete ad group source state	18	delete_adgroupsourcestate
57	Can add ad group source settings	19	add_adgroupsourcesettings
58	Can change ad group source settings	19	change_adgroupsourcesettings
59	Can delete ad group source settings	19	delete_adgroupsourcesettings
60	Can add upload batch	20	add_uploadbatch
61	Can change upload batch	20	change_uploadbatch
62	Can delete upload batch	20	delete_uploadbatch
63	Can add content ad	21	add_contentad
64	Can change content ad	21	change_contentad
65	Can delete content ad	21	delete_contentad
66	Can add content ad source	22	add_contentadsource
67	Can change content ad source	22	change_contentadsource
68	Can delete content ad source	22	delete_contentadsource
69	Can add article	23	add_article
70	Can change article	23	change_article
71	Can delete article	23	delete_article
72	Can add campaign budget settings	24	add_campaignbudgetsettings
73	Can change campaign budget settings	24	change_campaignbudgetsettings
74	Can delete campaign budget settings	24	delete_campaignbudgetsettings
75	Can add conversion pixel	25	add_conversionpixel
76	Can change conversion pixel	25	change_conversionpixel
77	Can delete conversion pixel	25	delete_conversionpixel
78	Can add conversion goal	26	add_conversiongoal
79	Can change conversion goal	26	change_conversiongoal
80	Can delete conversion goal	26	delete_conversiongoal
81	Can add demo ad group real ad group	27	add_demoadgrouprealadgroup
82	Can change demo ad group real ad group	27	change_demoadgrouprealadgroup
83	Can delete demo ad group real ad group	27	delete_demoadgrouprealadgroup
84	Can add user	28	add_user
85	Can change user	28	change_user
86	Can delete user	28	delete_user
87	Can view campaign's settings tab.	28	campaign_settings_view
88	Can view campaign's agency tab.	28	campaign_agency_view
89	Can view campaign's ad groups tab in dashboard.	28	campaign_ad_groups_view
90	Can be chosen as account manager.	28	campaign_settings_account_manager
91	Can be chosen as sales representative.	28	campaign_settings_sales_rep
92	Can view supply dash link.	28	supply_dash_link_view
93	Can view ad group's agency tab.	28	ad_group_agency_tab_view
94	Can view all accounts's accounts tab.	28	all_accounts_accounts_view
95	Can view accounts's campaigns tab.	28	account_campaigns_view
96	Can view accounts's agency tab.	28	account_agency_view
97	Can add media sources.	28	ad_group_sources_add_source
98	Can view campaign sources view.	28	campaign_sources_view
99	Can view account sources view.	28	account_sources_view
100	Can view all accounts sources view.	28	all_accounts_sources_view
101	Can add ad groups.	28	campaign_ad_groups_add_ad_group
102	Can add campaigns.	28	account_campaigns_add_campaign
103	Can add accounts.	28	all_accounts_accounts_add_account
104	Can see new sidebar.	28	all_new_sidebar
105	Can do campaign budget management.	28	campaign_budget_management_view
106	Can view account budget.	28	account_budget_view
107	Can view all accounts budget.	28	all_accounts_budget_view
108	Can archive or restore an entity.	28	archive_restore_entity
109	Can view archived entities.	28	view_archived_entities
110	Can view unspent budget.	28	unspent_budget_view
111	Can switch to demo mode.	28	switch_to_demo_mode
112	Can view and set account access permissions.	28	account_agency_access_permissions
113	New users are added to this group.	28	group_new_user_add
114	Can set per-source settings.	28	set_ad_group_source_settings
115	Can see current per-source state.	28	see_current_ad_group_source_state
116	Can download detailed report on campaign level.	28	campaign_ad_groups_detailed_report
117	Can view content ads postclick acq. metrics.	28	content_ads_postclick_acquisition
118	Can view content ads postclick eng. metrics.	28	content_ads_postclick_engagement
119	Can view aggregate postclick acq. metrics.	28	aggregate_postclick_acquisition
120	Can view aggregate postclick eng. metrics.	28	aggregate_postclick_engagement
121	Can see data status column in table.	28	data_status_column
122	Can view new content ads tab.	28	new_content_ads_tab
123	Can filter sources	28	filter_sources
124	Can upload new content ads.	28	upload_content_ads
125	Can set status of content ads.	28	set_content_ad_status
126	Can download bulk content ad csv.	28	get_content_ad_csv
127	Can view and use bulk content ads actions.	28	content_ads_bulk_actions
128	Can toggle Google Analytics performance tracking.	28	can_toggle_ga_performance_tracking
129	Can toggle Adobe Analytics performance tracking.	28	can_toggle_adobe_performance_tracking
130	Can see media source status on submission status popover	28	can_see_media_source_status_on_submission_popover
131	Can set DMA targeting	28	can_set_dma_targeting
132	Can set media source to auto-pilot	28	can_set_media_source_to_auto_pilot
133	Can manage conversion pixels	28	manage_conversion_pixels
134	Automatically add media sources on ad group creation	28	add_media_sources_automatically
135	Can see intercom widget	28	has_intercom
136	Can see publishers	28	can_see_publishers
137	Can manage conversion goals on campaign level	28	manage_conversion_goals
138	Can see Redshift postclick statistics	28	can_see_redshift_postclick_statistics
139	Automatic campaign stop on depleted budget applies to campaigns in this group	28	group_campaign_stop_on_budget_depleted
140	Can add internal group	29	add_internalgroup
141	Can change internal group	29	change_internalgroup
142	Can delete internal group	29	delete_internalgroup
143	Can add action log order	30	add_actionlogorder
144	Can change action log order	30	change_actionlogorder
145	Can delete action log order	30	delete_actionlogorder
146	Can add action log	31	add_actionlog
147	Can change action log	31	change_actionlog
148	Can delete action log	31	delete_actionlog
149	Can view manual ActionLog actions	31	manual_view
150	Can acknowledge manual ActionLog actions	31	manual_acknowledge
151	Can add article stats	32	add_articlestats
152	Can change article stats	32	change_articlestats
153	Can delete article stats	32	delete_articlestats
154	Can add goal conversion stats	33	add_goalconversionstats
155	Can change goal conversion stats	33	change_goalconversionstats
156	Can delete goal conversion stats	33	delete_goalconversionstats
157	Can add ad group stats	34	add_adgroupstats
158	Can change ad group stats	34	change_adgroupstats
159	Can delete ad group stats	34	delete_adgroupstats
160	Can add ad group goal conversion stats	35	add_adgroupgoalconversionstats
161	Can change ad group goal conversion stats	35	change_adgroupgoalconversionstats
162	Can delete ad group goal conversion stats	35	delete_adgroupgoalconversionstats
163	Can add content ad stats	36	add_contentadstats
164	Can change content ad stats	36	change_contentadstats
165	Can delete content ad stats	36	delete_contentadstats
166	Can add supply report recipient	37	add_supplyreportrecipient
167	Can change supply report recipient	37	change_supplyreportrecipient
168	Can delete supply report recipient	37	delete_supplyreportrecipient
169	Can add content ad postclick stats	38	add_contentadpostclickstats
170	Can change content ad postclick stats	38	change_contentadpostclickstats
171	Can delete content ad postclick stats	38	delete_contentadpostclickstats
172	Can add content ad goal conversion stats	39	add_contentadgoalconversionstats
173	Can change content ad goal conversion stats	39	change_contentadgoalconversionstats
174	Can delete content ad goal conversion stats	39	delete_contentadgoalconversionstats
175	Can add raw postclick stats	40	add_rawpostclickstats
176	Can change raw postclick stats	40	change_rawpostclickstats
177	Can delete raw postclick stats	40	delete_rawpostclickstats
178	Can add raw goal conversion stats	41	add_rawgoalconversionstats
179	Can change raw goal conversion stats	41	change_rawgoalconversionstats
180	Can delete raw goal conversion stats	41	delete_rawgoalconversionstats
181	Can add ga report log	42	add_gareportlog
182	Can change ga report log	42	change_gareportlog
183	Can delete ga report log	42	delete_gareportlog
184	Can add report log	43	add_reportlog
185	Can change report log	43	change_reportlog
186	Can delete report log	43	delete_reportlog
187	Can add campaign budget depletion notification	44	add_campaignbudgetdepletionnotification
188	Can change campaign budget depletion notification	44	change_campaignbudgetdepletionnotification
189	Can delete campaign budget depletion notification	44	delete_campaignbudgetdepletionnotification
190	Can add autopilot ad group source bid cpc log	45	add_autopilotadgroupsourcebidcpclog
191	Can change autopilot ad group source bid cpc log	45	change_autopilotadgroupsourcebidcpclog
192	Can delete autopilot ad group source bid cpc log	45	delete_autopilotadgroupsourcebidcpclog
193	Can add user action log	46	add_useractionlog
194	Can change user action log	46	change_useractionlog
195	Can delete user action log	46	delete_useractionlog
196	Can add publisher blacklist	47	add_publisherblacklist
197	Can change publisher blacklist	47	change_publisherblacklist
198	Can delete publisher blacklist	47	delete_publisherblacklist
199	Can add credit line item	48	add_creditlineitem
200	Can change credit line item	48	change_creditlineitem
201	Can delete credit line item	48	delete_creditlineitem
202	Can add budget line item	49	add_budgetlineitem
203	Can change budget line item	49	change_budgetlineitem
204	Can delete budget line item	49	delete_budgetlineitem
205	Can add credit history	50	add_credithistory
206	Can change credit history	50	change_credithistory
207	Can delete credit history	50	delete_credithistory
208	Can add budget history	51	add_budgethistory
209	Can change budget history	51	change_budgethistory
210	Can delete budget history	51	delete_budgethistory
211	Can add export report	52	add_exportreport
212	Can change export report	52	change_exportreport
213	Can delete export report	52	delete_exportreport
214	Can add scheduled export report	53	add_scheduledexportreport
215	Can change scheduled export report	53	change_scheduledexportreport
216	Can delete scheduled export report	53	delete_scheduledexportreport
217	Can add scheduled export report recipient	54	add_scheduledexportreportrecipient
218	Can change scheduled export report recipient	54	change_scheduledexportreportrecipient
219	Can delete scheduled export report recipient	54	delete_scheduledexportreportrecipient
220	Can view campaign's budget tab.	28	campaign_budget_view
221	Can view accounts's credit tab.	28	account_credit_view
222	Can set subdivision targeting	28	can_set_subdivision_targeting
223	Can see publishers blacklist status	28	can_see_publisher_blacklist_status
224	Can modify publishers blacklist status	28	can_modify_publisher_blacklist_status
225	Can see conversions and goals in reports	28	conversion_reports
226	Can download reports using new export facilities	28	exports_plus
227	Can view or access global/account/campaign publishers blacklist status	28	can_access_global_publisher_blacklist_status
\.


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('auth_permission_id_seq', 227, true);


--
-- Data for Name: automation_autopilotadgroupsourcebidcpclog; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY automation_autopilotadgroupsourcebidcpclog (id, created_dt, yesterdays_spend_cc, previous_cpc_cc, new_cpc_cc, current_daily_budget_cc, ad_group_id, ad_group_source_id, campaign_id, yesterdays_clicks, comments) FROM stdin;
\.


--
-- Name: automation_autopilotadgroupsourcebidcpclog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('automation_autopilotadgroupsourcebidcpclog_id_seq', 1, false);


--
-- Data for Name: automation_campaignbudgetdepletionnotification; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY automation_campaignbudgetdepletionnotification (id, created_dt, available_budget, yesterdays_spend, account_manager_id, campaign_id, stopped) FROM stdin;
\.


--
-- Name: automation_campaignbudgetdepletionnotification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('automation_campaignbudgetdepletionnotification_id_seq', 1, false);


--
-- Data for Name: convapi_gareportlog; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY convapi_gareportlog (id, datetime, for_date, email_subject, csv_filename, ad_groups, visits_reported, visits_imported, state, errors, multimatch, multimatch_clicks, nomatch, from_address, s3_key) FROM stdin;
\.


--
-- Name: convapi_gareportlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('convapi_gareportlog_id_seq', 1, false);


--
-- Data for Name: convapi_rawgoalconversionstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY convapi_rawgoalconversionstats (id, datetime, ad_group_id, source_id, url_raw, url_clean, device_type, goal_name, z1_adgid, z1_msid, conversions, conversions_value_cc) FROM stdin;
\.


--
-- Name: convapi_rawgoalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('convapi_rawgoalconversionstats_id_seq', 1, false);


--
-- Data for Name: convapi_rawpostclickstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY convapi_rawpostclickstats (id, datetime, ad_group_id, source_id, url_raw, url_clean, device_type, z1_adgid, z1_msid, visits, new_visits, bounced_visits, pageviews, duration) FROM stdin;
\.


--
-- Name: convapi_rawpostclickstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('convapi_rawpostclickstats_id_seq', 1, false);


--
-- Data for Name: convapi_reportlog; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY convapi_reportlog (id, datetime, for_date, email_subject, from_address, report_filename, visits_reported, visits_imported, state, errors, s3_key) FROM stdin;
\.


--
-- Name: convapi_reportlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('convapi_reportlog_id_seq', 1, false);


--
-- Data for Name: dash_account; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_account (id, name, created_dt, modified_dt, modified_by_id, outbrain_marketer_id) FROM stdin;
\.


--
-- Data for Name: dash_account_groups; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_account_groups (id, account_id, group_id) FROM stdin;
\.


--
-- Name: dash_account_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_account_groups_id_seq', 1, false);


--
-- Name: dash_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_account_id_seq', 1, false);


--
-- Data for Name: dash_account_users; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_account_users (id, account_id, user_id) FROM stdin;
\.


--
-- Name: dash_account_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_account_users_id_seq', 1, false);


--
-- Data for Name: dash_accountsettings; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_accountsettings (id, name, created_dt, archived, account_id, created_by_id, changes_text, default_account_manager_id, default_sales_representative_id, service_fee) FROM stdin;
\.


--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_accountsettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroup; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_adgroup (id, name, created_dt, modified_dt, modified_by_id, campaign_id, is_demo, content_ads_tab_with_cms) FROM stdin;
\.


--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_adgroup_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsettings; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_adgroupsettings (id, created_dt, state, start_date, end_date, cpc_cc, daily_budget_cc, target_devices, target_regions, tracking_code, ad_group_id, created_by_id, archived, changes_text, brand_name, call_to_action, description, display_url, ad_group_name, enable_ga_tracking, adobe_tracking_param, enable_adobe_tracking) FROM stdin;
\.


--
-- Name: dash_adgroupsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_adgroupsettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsource; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_adgroupsource (id, source_campaign_key, ad_group_id, source_id, source_credentials_id, last_successful_sync_dt, can_manage_content_ads, source_content_ad_id, submission_errors, submission_status, last_successful_reports_sync_dt, last_successful_status_sync_dt) FROM stdin;
\.


--
-- Name: dash_adgroupsource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_adgroupsource_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsourcesettings; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_adgroupsourcesettings (id, created_dt, state, cpc_cc, daily_budget_cc, ad_group_source_id, created_by_id, autopilot_state) FROM stdin;
\.


--
-- Name: dash_adgroupsourcesettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_adgroupsourcesettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsourcestate; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_adgroupsourcestate (id, created_dt, state, cpc_cc, daily_budget_cc, ad_group_source_id) FROM stdin;
\.


--
-- Name: dash_adgroupsourcestate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_adgroupsourcestate_id_seq', 1, false);


--
-- Data for Name: dash_article; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_article (id, url, title, created_dt, ad_group_id) FROM stdin;
\.


--
-- Name: dash_article_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_article_id_seq', 1, false);


--
-- Data for Name: dash_budgethistory; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_budgethistory (id, snapshot, created_dt, budget_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_budgethistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_budgethistory_id_seq', 1, false);


--
-- Data for Name: dash_budgetlineitem; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_budgetlineitem (id, start_date, end_date, amount, comment, created_dt, modified_dt, campaign_id, created_by_id, credit_id) FROM stdin;
\.


--
-- Name: dash_budgetlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_budgetlineitem_id_seq', 1, false);


--
-- Data for Name: dash_campaign; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_campaign (id, name, created_dt, modified_dt, account_id, modified_by_id) FROM stdin;
\.


--
-- Data for Name: dash_campaign_groups; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_campaign_groups (id, campaign_id, group_id) FROM stdin;
\.


--
-- Name: dash_campaign_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_campaign_groups_id_seq', 1, false);


--
-- Name: dash_campaign_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_campaign_id_seq', 1, false);


--
-- Data for Name: dash_campaign_users; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_campaign_users (id, campaign_id, user_id) FROM stdin;
\.


--
-- Name: dash_campaign_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_campaign_users_id_seq', 1, false);


--
-- Data for Name: dash_campaignbudgetsettings; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_campaignbudgetsettings (id, allocate, revoke, total, comment, created_dt, campaign_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_campaignbudgetsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_campaignbudgetsettings_id_seq', 1, false);


--
-- Data for Name: dash_campaignsettings; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_campaignsettings (id, created_dt, service_fee, iab_category, promotion_goal, account_manager_id, campaign_id, created_by_id, sales_representative_id, name, archived, campaign_goal, goal_quantity, changes_text) FROM stdin;
\.


--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_campaignsettings_id_seq', 1, false);


--
-- Data for Name: dash_contentad; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_contentad (id, image_id, batch_id, image_height, image_width, ad_group_id, created_dt, title, url, image_hash, state, redirect_id, archived, tracker_urls, brand_name, call_to_action, description, display_url, crop_areas) FROM stdin;
\.


--
-- Name: dash_contentad_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_contentad_id_seq', 1, false);


--
-- Data for Name: dash_contentadsource; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_contentadsource (id, submission_status, state, source_state, source_content_ad_id, created_dt, modified_dt, content_ad_id, source_id, submission_errors) FROM stdin;
\.


--
-- Name: dash_contentadsource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_contentadsource_id_seq', 1, false);


--
-- Data for Name: dash_conversiongoal; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_conversiongoal (id, type, name, conversion_window, goal_id, created_dt, campaign_id, pixel_id) FROM stdin;
\.


--
-- Name: dash_conversiongoal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_conversiongoal_id_seq', 1, false);


--
-- Data for Name: dash_conversionpixel; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_conversionpixel (id, slug, archived, created_dt, account_id, last_sync_dt) FROM stdin;
\.


--
-- Name: dash_conversionpixel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_conversionpixel_id_seq', 1, false);


--
-- Data for Name: dash_credithistory; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_credithistory (id, snapshot, created_dt, created_by_id, credit_id) FROM stdin;
\.


--
-- Name: dash_credithistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_credithistory_id_seq', 1, false);


--
-- Data for Name: dash_creditlineitem; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_creditlineitem (id, start_date, end_date, amount, license_fee, status, comment, created_dt, modified_dt, account_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_creditlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_creditlineitem_id_seq', 1, false);


--
-- Data for Name: dash_defaultsourcesettings; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_defaultsourcesettings (id, credentials_id, source_id, params, auto_add, daily_budget_cc, default_cpc_cc, mobile_cpc_cc) FROM stdin;
\.


--
-- Name: dash_defaultsourcesettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_defaultsourcesettings_id_seq', 1, false);


--
-- Data for Name: dash_demoadgrouprealadgroup; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_demoadgrouprealadgroup (id, multiplication_factor, demo_ad_group_id, real_ad_group_id) FROM stdin;
\.


--
-- Name: dash_demoadgrouprealadgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_demoadgrouprealadgroup_id_seq', 1, false);


--
-- Data for Name: dash_exportreport; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_exportreport (id, created_dt, granularity, breakdown_by_day, breakdown_by_source, order_by, additional_fields, account_id, ad_group_id, campaign_id, created_by_id) FROM stdin;
\.


--
-- Data for Name: dash_exportreport_filtered_sources; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_exportreport_filtered_sources (id, exportreport_id, source_id) FROM stdin;
\.


--
-- Name: dash_exportreport_filtered_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_exportreport_filtered_sources_id_seq', 1, false);


--
-- Name: dash_exportreport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_exportreport_id_seq', 1, false);


--
-- Data for Name: dash_outbrainaccount; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_outbrainaccount (id, marketer_id, created_dt, modified_dt, used) FROM stdin;
\.


--
-- Name: dash_outbrainaccount_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_outbrainaccount_id_seq', 1, false);


--
-- Data for Name: dash_publisherblacklist; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_publisherblacklist (id, name, ad_group_id, source_id, status, created_dt, account_id, campaign_id, everywhere) FROM stdin;
\.


--
-- Name: dash_publisherblacklist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_publisherblacklist_id_seq', 1, false);


--
-- Data for Name: dash_scheduledexportreport; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_scheduledexportreport (id, name, created_dt, state, sending_frequency, created_by_id, report_id) FROM stdin;
\.


--
-- Name: dash_scheduledexportreport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_scheduledexportreport_id_seq', 1, false);


--
-- Data for Name: dash_scheduledexportreportrecipient; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_scheduledexportreportrecipient (id, email, scheduled_report_id) FROM stdin;
\.


--
-- Name: dash_scheduledexportreportrecipient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_scheduledexportreportrecipient_id_seq', 1, false);


--
-- Data for Name: dash_source; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_source (id, name, maintenance, created_dt, modified_dt, source_type_id, tracking_slug, bidder_slug, deprecated, content_ad_submission_type) FROM stdin;
\.


--
-- Name: dash_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_source_id_seq', 1, false);


--
-- Data for Name: dash_sourcecredentials; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_sourcecredentials (id, name, credentials, created_dt, modified_dt, source_id) FROM stdin;
\.


--
-- Name: dash_sourcecredentials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_sourcecredentials_id_seq', 1, false);


--
-- Data for Name: dash_sourcetype; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_sourcetype (id, type, min_cpc, min_daily_budget, max_cpc, max_daily_budget, cpc_decimal_places, delete_traffic_metrics_threshold, available_actions) FROM stdin;
\.


--
-- Name: dash_sourcetype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_sourcetype_id_seq', 1, false);


--
-- Data for Name: dash_uploadbatch; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_uploadbatch (id, name, created_dt, status, error_report_key, num_errors, batch_size, processed_content_ads, inserted_content_ads) FROM stdin;
\.


--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_uploadbatch_id_seq', 1, false);


--
-- Data for Name: dash_useractionlog; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY dash_useractionlog (id, action_type, created_dt, account_id, account_settings_id, ad_group_id, ad_group_settings_id, campaign_id, campaign_settings_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_useractionlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('dash_useractionlog_id_seq', 1, false);


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 1, false);


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	dash	outbrainaccount
7	dash	account
8	dash	campaign
9	dash	accountsettings
10	dash	campaignsettings
11	dash	sourcetype
12	dash	source
13	dash	sourcecredentials
14	dash	defaultsourcesettings
15	dash	adgroup
16	dash	adgroupsource
17	dash	adgroupsettings
18	dash	adgroupsourcestate
19	dash	adgroupsourcesettings
20	dash	uploadbatch
21	dash	contentad
22	dash	contentadsource
23	dash	article
24	dash	campaignbudgetsettings
25	dash	conversionpixel
26	dash	conversiongoal
27	dash	demoadgrouprealadgroup
28	zemauth	user
29	zemauth	internalgroup
30	actionlog	actionlogorder
31	actionlog	actionlog
32	reports	articlestats
33	reports	goalconversionstats
34	reports	adgroupstats
35	reports	adgroupgoalconversionstats
36	reports	contentadstats
37	reports	supplyreportrecipient
38	reports	contentadpostclickstats
39	reports	contentadgoalconversionstats
40	convapi	rawpostclickstats
41	convapi	rawgoalconversionstats
42	convapi	gareportlog
43	convapi	reportlog
44	automation	campaignbudgetdepletionnotification
45	automation	autopilotadgroupsourcebidcpclog
46	dash	useractionlog
47	dash	publisherblacklist
48	dash	creditlineitem
49	dash	budgetlineitem
50	dash	credithistory
51	dash	budgethistory
52	dash	exportreport
53	dash	scheduledexportreport
54	dash	scheduledexportreportrecipient
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('django_content_type_id_seq', 54, true);


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2015-10-07 09:38:30.912574+00
2	auth	0001_initial	2015-10-07 09:38:31.54084+00
3	zemauth	0001_squashed_0038_auto_20150108_1153	2015-10-07 09:38:32.652814+00
4	dash	0001_squashed_0061_auto_20141211_1714	2015-10-07 09:38:42.463779+00
5	dash	0002_auto_20150119_1321	2015-10-07 09:38:42.538282+00
6	dash	0003_source_tracking_slug	2015-10-07 09:38:42.602868+00
7	dash	0004_auto_20150127_0952	2015-10-07 09:38:42.661624+00
8	dash	0005_auto_20150127_1011	2015-10-07 09:38:42.720818+00
9	dash	0006_outbrainaccount	2015-10-07 09:38:42.74731+00
10	dash	0007_account_outbrain_account	2015-10-07 09:38:42.824839+00
11	dash	0008_auto_20150204_1622	2015-10-07 09:38:42.940026+00
12	dash	0009_account_outbrain_marketer_id	2015-10-07 09:38:42.996926+00
13	dash	0010_sourcetype_cpc_decimal_places	2015-10-07 09:38:43.056592+00
14	dash	0011_auto_20150217_0933	2015-10-07 09:38:43.400764+00
15	dash	0012_auto_20150217_1342	2015-10-07 09:38:43.613174+00
16	dash	0013_auto_20150220_1234	2015-10-07 09:38:43.817358+00
17	dash	0014_source_bidder_slug	2015-10-07 09:38:43.890011+00
18	dash	0014_auto_20150223_1404	2015-10-07 09:38:44.085611+00
19	dash	0015_merge	2015-10-07 09:38:44.094076+00
20	dash	0016_auto_20150224_1041	2015-10-07 09:38:44.272797+00
21	dash	0017_contentadsource_submission_errors	2015-10-07 09:38:44.351199+00
22	dash	0018_auto_20150225_1353	2015-10-07 09:38:44.441804+00
23	actionlog	0001_initial	2015-10-07 09:38:44.457032+00
24	actionlog	0002_auto_20140716_2233	2015-10-07 09:38:44.703126+00
25	actionlog	0003_auto_20140725_1235	2015-10-07 09:38:44.991475+00
26	actionlog	0004_auto_20140814_1418	2015-10-07 09:38:45.080525+00
27	actionlog	0005_auto_20140903_1537	2015-10-07 09:38:45.174643+00
28	actionlog	0005_auto_20140903_1234	2015-10-07 09:38:45.270415+00
29	actionlog	0006_merge	2015-10-07 09:38:45.280234+00
30	actionlog	0007_auto_20140922_1619	2015-10-07 09:38:45.539392+00
31	actionlog	0007_auto_20140919_1012	2015-10-07 09:38:46.562718+00
32	actionlog	0008_merge	2015-10-07 09:38:46.571997+00
33	actionlog	0009_auto_20141117_1236	2015-10-07 09:38:46.719848+00
34	actionlog	0010_auto_20141124_1426	2015-10-07 09:38:46.784491+00
35	actionlog	0010_auto_20141121_1714	2015-10-07 09:38:46.847675+00
36	actionlog	0011_merge	2015-10-07 09:38:46.856028+00
37	actionlog	0012_auto_20141205_1332	2015-10-07 09:38:46.936866+00
38	actionlog	0013_auto_20150224_0846	2015-10-07 09:38:47.000851+00
39	actionlog	0014_actionlog_content_ad_source	2015-10-07 09:38:47.075518+00
40	actionlog	0015_auto_20150227_1416	2015-10-07 09:38:47.142505+00
41	actionlog	0016_auto_20150326_1532	2015-10-07 09:38:47.20829+00
42	actionlog	0017_auto_20150331_1124	2015-10-07 09:38:47.277271+00
43	actionlog	0018_auto_20150422_1317	2015-10-07 09:38:47.342259+00
44	actionlog	0019_auto_20150523_1023	2015-10-07 09:38:47.408825+00
45	actionlog	0020_auto_20150918_1542	2015-10-07 09:38:47.475143+00
46	actionlog	0021_auto_20150922_0957	2015-10-07 09:38:47.538788+00
47	admin	0001_initial	2015-10-07 09:38:47.643762+00
48	contenttypes	0002_remove_content_type_name	2015-10-07 09:38:47.839071+00
49	auth	0002_alter_permission_name_max_length	2015-10-07 09:38:47.915127+00
50	auth	0003_alter_user_email_max_length	2015-10-07 09:38:47.986463+00
51	auth	0004_alter_user_username_opts	2015-10-07 09:38:48.059661+00
52	auth	0005_alter_user_last_login_null	2015-10-07 09:38:48.128116+00
53	auth	0006_require_contenttypes_0002	2015-10-07 09:38:48.134555+00
54	dash	0019_auto_20150226_1359	2015-10-07 09:38:48.202599+00
55	dash	0020_auto_20150227_1416	2015-10-07 09:38:48.594618+00
56	dash	0021_auto_20150227_1434	2015-10-07 09:38:48.675729+00
57	dash	0022_auto_20150303_1802	2015-10-07 09:38:48.81948+00
58	dash	0023_auto_20150316_0942	2015-10-07 09:38:49.125079+00
59	dash	0024_auto_20150323_1127	2015-10-07 09:38:49.21492+00
60	dash	0025_auto_20150331_1124	2015-10-07 09:38:49.820053+00
61	dash	0026_auto_20150331_1215	2015-10-07 09:38:49.835519+00
62	dash	0027_auto_20150331_1220	2015-10-07 09:38:50.100487+00
63	dash	0028_auto_20150331_1354	2015-10-07 09:38:50.201619+00
64	dash	0025_auto_20150407_1330	2015-10-07 09:38:50.315857+00
65	dash	0026_auto_20150408_0853	2015-10-07 09:38:50.429949+00
66	dash	0027_auto_20150408_1343	2015-10-07 09:38:50.65137+00
67	dash	0029_merge	2015-10-07 09:38:50.659566+00
68	dash	0030_contentad_image_hash	2015-10-07 09:38:50.763438+00
69	dash	0031_auto_20150417_1202	2015-10-07 09:38:50.855456+00
70	dash	0032_auto_20150417_1253	2015-10-07 09:38:50.97069+00
71	dash	0033_auto_20150420_0953	2015-10-07 09:38:51.288622+00
72	dash	0034_auto_20150421_1329	2015-10-07 09:38:51.478568+00
73	dash	0035_uploadbatch_error_report_key	2015-10-07 09:38:51.582907+00
74	dash	0036_uploadbatch_num_errors	2015-10-07 09:38:51.688346+00
75	dash	0037_contentad_state	2015-10-07 09:38:51.824155+00
76	dash	0038_auto_20150504_1454	2015-10-07 09:38:51.840384+00
77	dash	0037_adgroup_content_ads_tab_with_cms	2015-10-07 09:38:52.72263+00
78	dash	0039_merge	2015-10-07 09:38:52.730172+00
79	dash	0037_adgroupsource_can_manage_content_ads	2015-10-07 09:38:52.846912+00
80	dash	0038_auto_20150430_1510	2015-10-07 09:38:52.863142+00
81	dash	0040_merge	2015-10-07 09:38:52.871777+00
82	dash	0037_auto_20150504_1724	2015-10-07 09:38:53.326954+00
83	dash	0038_auto_20150504_1928	2015-10-07 09:38:53.34703+00
84	dash	0041_merge	2015-10-07 09:38:53.358064+00
85	dash	0042_auto_20150504_2037	2015-10-07 09:38:53.450873+00
86	dash	0035_auto_20150422_1317	2015-10-07 09:38:53.7957+00
87	dash	0037_merge	2015-10-07 09:38:53.803705+00
88	dash	0043_merge	2015-10-07 09:38:53.811109+00
89	dash	0044_auto_20150511_1255	2015-10-07 09:38:53.966166+00
90	dash	0045_auto_20150511_1259	2015-10-07 09:38:53.987747+00
91	dash	0046_auto_20150523_1023	2015-10-07 09:38:54.374077+00
92	dash	0047_auto_20150528_1452	2015-10-07 09:38:54.470283+00
93	dash	0048_auto_20150528_1503	2015-10-07 09:38:54.494269+00
94	dash	0047_contentad_redirect_id	2015-10-07 09:38:54.594008+00
95	dash	0049_merge	2015-10-07 09:38:54.599286+00
96	dash	0050_uploadbatch_inc_desc	2015-10-07 09:38:54.787745+00
97	dash	0051_auto_20150602_1030	2015-10-07 09:38:54.881748+00
98	dash	0052_auto_20150602_1422	2015-10-07 09:38:54.90755+00
99	dash	0053_auto_20150603_1705	2015-10-07 09:38:55.090604+00
100	dash	0054_contentad_archived	2015-10-07 09:38:55.21764+00
101	dash	0055_adgroupsettings_enable_ga_tracking	2015-10-07 09:38:55.348006+00
102	dash	0056_auto_20150630_1154	2015-10-07 09:38:55.532839+00
103	dash	0057_contentad_tracker_urls	2015-10-07 09:38:55.638871+00
104	dash	0058_auto_20150707_0945	2015-10-07 09:38:55.756044+00
105	dash	0059_sourcetype_available_actions_new	2015-10-07 09:38:55.861714+00
106	dash	0060_source_actions_data_migration	2015-10-07 09:38:55.875069+00
107	dash	0061_auto_20150721_1158	2015-10-07 09:38:55.991925+00
108	dash	0062_sourcetype_available_actions	2015-10-07 09:38:56.093877+00
109	dash	0063_source_actions_data_migration	2015-10-07 09:38:56.109462+00
110	dash	0064_remove_sourcetype_available_actions_new	2015-10-07 09:38:56.208084+00
111	dash	0065_auto_20150909_1206	2015-10-07 09:38:56.336675+00
112	automation	0001_initial	2015-10-07 09:38:56.46761+00
113	automation	0002_auto_20150819_1127	2015-10-07 09:38:56.847099+00
114	automation	0003_auto_20150819_1134	2015-10-07 09:38:56.949112+00
115	automation	0004_auto_20150826_1326	2015-10-07 09:38:57.360125+00
116	automation	0005_proposedadgroupsourcebidcpc	2015-10-07 09:38:57.515261+00
117	automation	0006_auto_20150908_1444	2015-10-07 09:38:57.935255+00
118	automation	0007_proposedadgroupsourcebidcpc	2015-10-07 09:38:58.085842+00
119	automation	0008_auto_20150909_1240	2015-10-07 09:38:58.603368+00
120	automation	0009_autopilotadgroupsourcebidcpclog_yesterdays_clicks	2015-10-07 09:38:58.719012+00
121	automation	0010_campaignbudgetdepletionnotification_stopped	2015-10-07 09:38:58.856667+00
122	automation	0010_autopilotadgroupsourcebidcpclog_comments	2015-10-07 09:38:58.976397+00
123	automation	0011_merge	2015-10-07 09:38:58.983891+00
124	convapi	0001_initial	2015-10-07 09:38:59.078871+00
125	convapi	0002_auto_20140915_1036	2015-10-07 09:38:59.140335+00
126	convapi	0003_auto_20140929_1003	2015-10-07 09:38:59.172719+00
127	convapi	0004_gareportlog	2015-10-07 09:38:59.210473+00
128	convapi	0005_auto_20141203_1427	2015-10-07 09:38:59.233091+00
129	convapi	0006_auto_20141204_1630	2015-10-07 09:38:59.34209+00
130	convapi	0007_gareportlog_from_address	2015-10-07 09:38:59.362754+00
131	convapi	0008_auto_20150729_1054	2015-10-07 09:38:59.447921+00
132	convapi	0009_reportlog	2015-10-07 09:38:59.484694+00
133	convapi	0010_auto_20150923_0913	2015-10-07 09:38:59.520772+00
134	dash	0065_auto_20150820_1418	2015-10-07 09:38:59.744977+00
135	dash	0066_auto_20150821_1437	2015-10-07 09:39:00.797285+00
136	dash	0065_auto_20150828_1151	2015-10-07 09:39:01.003432+00
137	dash	0066_add_batch_fields_to_contentad	2015-10-07 09:39:01.552981+00
138	dash	0067_merge	2015-10-07 09:39:01.559632+00
139	dash	0068_auto_20150908_0901	2015-10-07 09:39:01.673132+00
140	dash	0069_auto_20150908_1211	2015-10-07 09:39:01.760909+00
141	dash	0070_conversionpixel_last_sync_dt	2015-10-07 09:39:01.865463+00
142	dash	0071_remove_batch_fields	2015-10-07 09:39:02.23897+00
143	dash	0072_auto_20150911_1004	2015-10-07 09:39:02.42946+00
144	dash	0072_auto_20150910_1547	2015-10-07 09:39:02.706154+00
145	dash	0073_merge	2015-10-07 09:39:03.145213+00
146	dash	0066_adgroupsourcesettings_autopilot	2015-10-07 09:39:03.278283+00
147	dash	0074_merge	2015-10-07 09:39:03.284384+00
148	dash	0075_auto_20150916_1005	2015-10-07 09:39:03.502949+00
149	dash	0076_auto_20150925_0813	2015-10-07 09:39:03.840353+00
150	reports	0001_initial	2015-10-07 09:39:03.849732+00
151	reports	0002_auto_20140716_2233	2015-10-07 09:39:04.105413+00
152	reports	0003_auto_20140801_1326	2015-10-07 09:39:04.220299+00
153	reports	0004_auto_20140805_1602	2015-10-07 09:39:04.337784+00
154	reports	0005_auto_20140808_1646	2015-10-07 09:39:04.44993+00
155	reports	0006_auto_20140903_1537	2015-10-07 09:39:05.795022+00
156	reports	0007_auto_20140904_0648	2015-10-07 09:39:06.073349+00
157	reports	0008_auto_20141001_1501	2015-10-07 09:39:07.04369+00
158	reports	0009_auto_20141112_1044	2015-10-07 09:39:07.224114+00
159	reports	0009_auto_20141110_1510	2015-10-07 09:39:07.397275+00
160	reports	0010_merge	2015-10-07 09:39:07.443079+00
161	reports	0011_auto_20141204_1110	2015-10-07 09:39:07.754565+00
162	reports	0012_auto_20150323_1611	2015-10-07 09:39:09.534686+00
163	reports	0013_auto_20150326_1417	2015-10-07 09:39:09.788516+00
164	reports	0014_auto_20150326_1532	2015-10-07 09:39:10.08307+00
165	reports	0015_auto_20150409_0901	2015-10-07 09:39:10.695057+00
166	reports	0016_supplyreportrecipient	2015-10-07 09:39:11.154442+00
167	reports	0017_auto_20150817_1343	2015-10-07 09:39:12.403745+00
168	reports	0018_auto_20150826_1449	2015-10-07 09:39:13.254269+00
169	reports	0019_auto_20150826_1453	2015-10-07 09:39:13.602481+00
170	reports	0020_auto_20150908_1655	2015-10-07 09:39:14.105095+00
171	reports	0021_auto_20150923_1124	2015-10-07 09:39:14.29418+00
172	sessions	0001_initial	2015-10-07 09:39:14.654236+00
173	zemauth	0002_auto_20150211_1558	2015-10-07 09:39:14.859144+00
174	zemauth	0002_auto_20150209_1106	2015-10-07 09:39:15.036785+00
175	zemauth	0003_merge	2015-10-07 09:39:15.082353+00
176	zemauth	0004_auto_20150318_1655	2015-10-07 09:39:15.259855+00
177	zemauth	0005_auto_20150504_1718	2015-10-07 09:39:15.442573+00
178	zemauth	0006_auto_20150523_1023	2015-10-07 09:39:15.924167+00
179	zemauth	0007_auto_20150602_1353	2015-10-07 09:39:16.061042+00
180	zemauth	0008_auto_20150604_1000	2015-10-07 09:39:16.206048+00
181	zemauth	0009_auto_20150608_0959	2015-10-07 09:39:16.339046+00
182	zemauth	0010_auto_20150629_0938	2015-10-07 09:39:16.476855+00
183	zemauth	0011_auto_20150702_1346	2015-10-07 09:39:16.61739+00
184	zemauth	0012_auto_20150703_0753	2015-10-07 09:39:16.76796+00
185	zemauth	0013_auto_20150708_1150	2015-10-07 09:39:16.910088+00
186	zemauth	0039_user_show_onboarding_guidance	2015-10-07 09:39:17.078055+00
187	zemauth	0014_auto_20150828_1151	2015-10-07 09:39:17.218704+00
188	zemauth	0040_merge	2015-10-07 09:39:17.228681+00
189	zemauth	0041_auto_20150904_0844	2015-10-07 09:39:17.375255+00
190	zemauth	0042_auto_20150907_1448	2015-10-07 09:39:17.395036+00
191	zemauth	0043_auto_20150911_0835	2015-10-07 09:39:17.53334+00
192	zemauth	0043_auto_20150910_1339	2015-10-07 09:39:17.680547+00
193	zemauth	0044_merge	2015-10-07 09:39:17.829017+00
194	zemauth	0014_auto_20150911_1009	2015-10-07 09:39:18.740545+00
195	zemauth	0043_merge	2015-10-07 09:39:18.751609+00
196	zemauth	0044_auto_20150911_1528	2015-10-07 09:39:18.85859+00
197	zemauth	0045_merge	2015-10-07 09:39:18.867223+00
198	zemauth	0046_auto_20150915_1520	2015-10-07 09:39:18.97585+00
199	zemauth	0045_auto_20150915_2141	2015-10-07 09:39:19.090677+00
200	zemauth	0047_merge	2015-10-07 09:39:19.097728+00
201	zemauth	0048_auto_20150916_1230	2015-10-07 09:39:19.221839+00
202	zemauth	0046_auto_20150917_1520	2015-10-07 09:39:19.348337+00
203	zemauth	0049_merge	2015-10-07 09:39:19.358189+00
204	zemauth	0046_auto_20150916_1414	2015-10-07 09:39:19.489565+00
205	zemauth	0050_merge	2015-10-07 09:39:19.497938+00
206	zemauth	0051_auto_20150922_0848	2015-10-07 09:39:19.618995+00
207	zemauth	0052_auto_20150922_0849	2015-10-07 09:39:19.738302+00
208	zemauth	0050_auto_20150922_0957	2015-10-07 09:39:19.861785+00
209	zemauth	0053_merge	2015-10-07 09:39:19.870952+00
210	zemauth	0051_auto_20150923_1124	2015-10-07 09:39:19.998754+00
211	zemauth	0054_merge	2015-10-07 09:39:20.008949+00
212	zemauth	0055_auto_20150924_1318	2015-10-07 09:39:20.132486+00
213	zemauth	0052_auto_20150925_0815	2015-10-07 09:39:20.258688+00
214	zemauth	0056_merge	2015-10-07 09:39:20.266269+00
215	zemauth	0057_auto_20150925_1513	2015-10-07 09:39:20.390933+00
216	zemauth	0058_auto_20151001_1429	2015-10-07 09:39:20.518307+00
217	actionlog	0022_auto_20151103_0957	2015-11-19 15:10:07.599958+00
218	dash	0077_accountsettings_service_fee	2015-11-19 15:10:08.30106+00
219	dash	0078_useractionlog	2015-11-19 15:10:09.120051+00
220	dash	0079_auto_20151028_1341	2015-11-19 15:10:09.388059+00
221	dash	0079_auto_20151014_1305	2015-11-19 15:10:09.991461+00
222	dash	0080_merge	2015-11-19 15:10:10.041657+00
223	dash	0079_uploadbatch_inserted_content_ads	2015-11-19 15:10:10.259837+00
224	dash	0081_merge	2015-11-19 15:10:10.34057+00
225	dash	0082_auto_20151103_0959	2015-11-19 15:10:12.309376+00
226	dash	0083_publisherblacklist_status	2015-11-19 15:10:12.800629+00
227	dash	0084_publisherblacklist_created_dt	2015-11-19 15:10:13.26046+00
228	dash	0084_contentad_crop_areas	2015-11-19 15:10:13.478519+00
229	dash	0083_scheduledreport_scheduledreportrecipient	2015-11-19 15:10:14.331689+00
230	dash	0084_auto_20151105_1455	2015-11-19 15:10:14.619511+00
231	dash	0085_merge	2015-11-19 15:10:14.668761+00
232	dash	0086_auto_20151109_1056	2015-11-19 15:10:15.219646+00
233	dash	0087_auto_20151111_1557	2015-11-19 15:10:17.601767+00
234	dash	0082_auto_20151030_1256	2015-11-19 15:10:18.811087+00
235	dash	0083_merge	2015-11-19 15:10:18.860412+00
236	dash	0084_merge	2015-11-19 15:10:18.908074+00
237	dash	0085_auto_20151106_1125	2015-11-19 15:10:19.138526+00
238	dash	0086_merge	2015-11-19 15:10:19.189844+00
239	dash	0088_merge	2015-11-19 15:10:19.240469+00
240	zemauth	0059_auto_20151012_1027	2015-11-19 15:10:19.428731+00
241	zemauth	0060_auto_20151014_1419	2015-11-19 15:10:19.608434+00
242	zemauth	0061_auto_20151102_1757	2015-11-19 15:10:19.791399+00
243	zemauth	0061_auto_20151029_0906	2015-11-19 15:10:20.115694+00
244	zemauth	0062_merge	2015-11-19 15:10:20.347076+00
245	zemauth	0063_auto_20151111_1039	2015-11-19 15:10:20.558123+00
246	zemauth	0064_auto_20151111_1520	2015-11-19 15:10:20.760925+00
247	zemauth	0065_auto_20151117_0923	2015-11-19 15:10:21.149468+00
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('django_migrations_id_seq', 247, true);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
75qbtp9dvxeb7hp9byprkhm85q84mfwk	NGNkN2U0MGQzOWNkMWMwYWJhNTI5ZjA0MjA4ZjBhNWUzZWIzY2NmZTp7Il9hdXRoX3VzZXJfaGFzaCI6IjBjMmY4ZGQyOGE1ZWUxYWNhZjhkNTFiYzQ4OGQ2NWZlZTE0ZGExMjQiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJ6ZW1hdXRoLmJhY2tlbmRzLkVtYWlsT3JVc2VybmFtZU1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIxIn0=	2015-12-03 15:10:39.998126+00
\.


--
-- Data for Name: reports_adgroupgoalconversionstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_adgroupgoalconversionstats (id, datetime, goal_name, conversions, conversions_value_cc, ad_group_id, source_id) FROM stdin;
\.


--
-- Name: reports_adgroupgoalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_adgroupgoalconversionstats_id_seq', 1, false);


--
-- Data for Name: reports_adgroupstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_adgroupstats (id, datetime, impressions, clicks, cost_cc, visits, new_visits, bounced_visits, pageviews, duration, has_traffic_metrics, has_postclick_metrics, has_conversion_metrics, created_dt, ad_group_id, source_id, data_cost_cc) FROM stdin;
\.


--
-- Name: reports_adgroupstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_adgroupstats_id_seq', 1, false);


--
-- Data for Name: reports_articlestats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_articlestats (id, datetime, impressions, clicks, cost_cc, created_dt, ad_group_id, article_id, source_id, bounced_visits, duration, has_postclick_metrics, has_traffic_metrics, new_visits, pageviews, visits, has_conversion_metrics, data_cost_cc) FROM stdin;
\.


--
-- Name: reports_articlestats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_articlestats_id_seq', 1, false);


--
-- Data for Name: reports_contentadgoalconversionstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_contentadgoalconversionstats (id, date, goal_type, goal_name, created_dt, content_ad_id, source_id, conversions) FROM stdin;
\.


--
-- Name: reports_contentadgoalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_contentadgoalconversionstats_id_seq', 1, false);


--
-- Data for Name: reports_contentadpostclickstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_contentadpostclickstats (id, date, created_dt, visits, new_visits, bounced_visits, pageviews, total_time_on_site, content_ad_id, source_id) FROM stdin;
\.


--
-- Name: reports_contentadpostclickstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_contentadpostclickstats_id_seq', 1, false);


--
-- Data for Name: reports_contentadstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_contentadstats (id, impressions, clicks, cost_cc, data_cost_cc, date, created_dt, content_ad_id, content_ad_source_id, source_id) FROM stdin;
\.


--
-- Name: reports_contentadstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_contentadstats_id_seq', 1, false);


--
-- Data for Name: reports_goalconversionstats; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_goalconversionstats (id, datetime, goal_name, conversions, conversions_value_cc, ad_group_id, article_id, source_id) FROM stdin;
\.


--
-- Name: reports_goalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_goalconversionstats_id_seq', 1, false);


--
-- Data for Name: reports_supplyreportrecipient; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY reports_supplyreportrecipient (id, first_name, last_name, email, created_dt, modified_dt, source_id) FROM stdin;
\.


--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('reports_supplyreportrecipient_id_seq', 1, false);


--
-- Data for Name: zemauth_internalgroup; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY zemauth_internalgroup (id, group_id) FROM stdin;
\.


--
-- Name: zemauth_internalgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('zemauth_internalgroup_id_seq', 1, false);


--
-- Data for Name: zemauth_user_groups; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY zemauth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Name: zemauth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('zemauth_user_groups_id_seq', 1, false);


--
-- Name: zemauth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('zemauth_user_id_seq', 1, true);


--
-- Data for Name: zemauth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: eins
--

COPY zemauth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Name: zemauth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: eins
--

SELECT pg_catalog.setval('zemauth_user_user_permissions_id_seq', 1, false);


--
-- Name: actionlog_actionlog_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_actionlog_pkey PRIMARY KEY (id);


--
-- Name: actionlog_actionlogorder_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY actionlog_actionlogorder
    ADD CONSTRAINT actionlog_actionlogorder_pkey PRIMARY KEY (id);


--
-- Name: auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions_group_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission_content_type_id_codename_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_key UNIQUE (content_type_id, codename);


--
-- Name: auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_autopilotadgroupsourcebidcpclog_pkey PRIMARY KEY (id);


--
-- Name: automation_campaignbudgetdepletionnotification_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_campaignbudgetdepletionnotification_pkey PRIMARY KEY (id);


--
-- Name: convapi_gareportlog_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY convapi_gareportlog
    ADD CONSTRAINT convapi_gareportlog_pkey PRIMARY KEY (id);


--
-- Name: convapi_rawgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY convapi_rawgoalconversionstats
    ADD CONSTRAINT convapi_rawgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: convapi_rawpostclickstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY convapi_rawpostclickstats
    ADD CONSTRAINT convapi_rawpostclickstats_pkey PRIMARY KEY (id);


--
-- Name: convapi_reportlog_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY convapi_reportlog
    ADD CONSTRAINT convapi_reportlog_pkey PRIMARY KEY (id);


--
-- Name: dash_account_groups_account_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_account_id_group_id_key UNIQUE (account_id, group_id);


--
-- Name: dash_account_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_pkey PRIMARY KEY (id);


--
-- Name: dash_account_name_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_name_key UNIQUE (name);


--
-- Name: dash_account_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_pkey PRIMARY KEY (id);


--
-- Name: dash_account_users_account_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_account_id_user_id_key UNIQUE (account_id, user_id);


--
-- Name: dash_account_users_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_pkey PRIMARY KEY (id);


--
-- Name: dash_accountsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsource_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsourcesettings_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgroupsourcesettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsourcestate_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_adgroupsourcestate
    ADD CONSTRAINT dash_adgroupsourcestate_pkey PRIMARY KEY (id);


--
-- Name: dash_article_ad_group_id_3e67a346ec46475b_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_ad_group_id_3e67a346ec46475b_uniq UNIQUE (ad_group_id, url, title);


--
-- Name: dash_article_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_pkey PRIMARY KEY (id);


--
-- Name: dash_budgethistory_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethistory_pkey PRIMARY KEY (id);


--
-- Name: dash_budgetlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlineitem_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_groups_campaign_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_campaign_id_group_id_key UNIQUE (campaign_id, group_id);


--
-- Name: dash_campaign_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_users_campaign_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_campaign_id_user_id_key UNIQUE (campaign_id, user_id);


--
-- Name: dash_campaign_users_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_pkey PRIMARY KEY (id);


--
-- Name: dash_campaignbudgetsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaignbudgetsettings
    ADD CONSTRAINT dash_campaignbudgetsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_campaignsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaignsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_contentad_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_pkey PRIMARY KEY (id);


--
-- Name: dash_contentadsource_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsource_pkey PRIMARY KEY (id);


--
-- Name: dash_conversiongoal_campaign_id_2f842d4d685c8de7_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_2f842d4d685c8de7_uniq UNIQUE (campaign_id, type, goal_id);


--
-- Name: dash_conversiongoal_campaign_id_4de26d291cfe92a0_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_4de26d291cfe92a0_uniq UNIQUE (campaign_id, pixel_id);


--
-- Name: dash_conversiongoal_campaign_id_62decd992187eef7_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_62decd992187eef7_uniq UNIQUE (campaign_id, name);


--
-- Name: dash_conversiongoal_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_pkey PRIMARY KEY (id);


--
-- Name: dash_conversionpixel_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_pkey PRIMARY KEY (id);


--
-- Name: dash_conversionpixel_slug_65b87bfffd455d67_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_slug_65b87bfffd455d67_uniq UNIQUE (slug, account_id);


--
-- Name: dash_credithistory_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithistory_pkey PRIMARY KEY (id);


--
-- Name: dash_creditlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlineitem_pkey PRIMARY KEY (id);


--
-- Name: dash_defaultsourcesettings_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_pkey PRIMARY KEY (id);


--
-- Name: dash_defaultsourcesettings_source_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_source_id_key UNIQUE (source_id);


--
-- Name: dash_demoadgrouprealadgroup_demo_ad_group_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoadgrouprealadgroup_demo_ad_group_id_key UNIQUE (demo_ad_group_id);


--
-- Name: dash_demoadgrouprealadgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoadgrouprealadgroup_pkey PRIMARY KEY (id);


--
-- Name: dash_demoadgrouprealadgroup_real_ad_group_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoadgrouprealadgroup_real_ad_group_id_key UNIQUE (real_ad_group_id);


--
-- Name: dash_exportreport_filtered_source_exportreport_id_source_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_source_exportreport_id_source_id_key UNIQUE (exportreport_id, source_id);


--
-- Name: dash_exportreport_filtered_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_sources_pkey PRIMARY KEY (id);


--
-- Name: dash_exportreport_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_pkey PRIMARY KEY (id);


--
-- Name: dash_outbrainaccount_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_outbrainaccount
    ADD CONSTRAINT dash_outbrainaccount_pkey PRIMARY KEY (id);


--
-- Name: dash_publisherblacklist_name_2eec92a070a4cbb8_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_name_2eec92a070a4cbb8_uniq UNIQUE (name, everywhere, account_id, campaign_id, ad_group_id, source_id);


--
-- Name: dash_publisherblacklist_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportr_scheduled_report_id_4d149aaafb5876bc_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT dash_scheduledexportr_scheduled_report_id_4d149aaafb5876bc_uniq UNIQUE (scheduled_report_id, email);


--
-- Name: dash_scheduledexportreport_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_scheduledexportreport_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportreportrecipient_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT dash_scheduledexportreportrecipient_pkey PRIMARY KEY (id);


--
-- Name: dash_source_bidder_slug_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_bidder_slug_key UNIQUE (bidder_slug);


--
-- Name: dash_source_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_pkey PRIMARY KEY (id);


--
-- Name: dash_source_tracking_slug_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_tracking_slug_key UNIQUE (tracking_slug);


--
-- Name: dash_sourcecredentials_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_sourcecredentials
    ADD CONSTRAINT dash_sourcecredentials_pkey PRIMARY KEY (id);


--
-- Name: dash_sourcetype_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_sourcetype
    ADD CONSTRAINT dash_sourcetype_pkey PRIMARY KEY (id);


--
-- Name: dash_sourcetype_type_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_sourcetype
    ADD CONSTRAINT dash_sourcetype_type_key UNIQUE (type);


--
-- Name: dash_uploadbatch_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_uploadbatch
    ADD CONSTRAINT dash_uploadbatch_pkey PRIMARY KEY (id);


--
-- Name: dash_useractionlog_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractionlog_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type_app_label_45f3b1d93ec8c61c_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_45f3b1d93ec8c61c_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: reports_adgroupgoalconversionsta_datetime_64c6effdb1878da9_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconversionsta_datetime_64c6effdb1878da9_uniq UNIQUE (datetime, ad_group_id, source_id, goal_name);


--
-- Name: reports_adgroupgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_adgroupstats_datetime_61985984b28519c1_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_datetime_61985984b28519c1_uniq UNIQUE (datetime, ad_group_id, source_id);


--
-- Name: reports_adgroupstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_pkey PRIMARY KEY (id);


--
-- Name: reports_articlestats_datetime_22035dbdd8455a0c_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_datetime_22035dbdd8455a0c_uniq UNIQUE (datetime, ad_group_id, article_id, source_id);


--
-- Name: reports_articlestats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadgoalconversionstats_date_2075955a8d03dddc_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconversionstats_date_2075955a8d03dddc_uniq UNIQUE (date, content_ad_id, source_id, goal_type, goal_name);


--
-- Name: reports_contentadgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadpostclickstats_date_2400403d2fcae43d_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclickstats_date_2400403d2fcae43d_uniq UNIQUE (date, content_ad_id, source_id);


--
-- Name: reports_contentadpostclickstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclickstats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadstats_date_4bd0def2cd7fded4_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_date_4bd0def2cd7fded4_uniq UNIQUE (date, content_ad_source_id);


--
-- Name: reports_contentadstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_pkey PRIMARY KEY (id);


--
-- Name: reports_goalconversionstats_datetime_1095ea069adf2ffd_uniq; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstats_datetime_1095ea069adf2ffd_uniq UNIQUE (datetime, ad_group_id, article_id, source_id, goal_name);


--
-- Name: reports_goalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_supplyreportrecipient_email_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyreportrecipient_email_key UNIQUE (email);


--
-- Name: reports_supplyreportrecipient_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyreportrecipient_pkey PRIMARY KEY (id);


--
-- Name: zemauth_internalgroup_group_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_group_id_key UNIQUE (group_id);


--
-- Name: zemauth_internalgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: zemauth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_user
    ADD CONSTRAINT zemauth_user_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: eins; Tablespace:
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: actionlog_actionlog_69dfcb07; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_69dfcb07 ON actionlog_actionlog USING btree (order_id);


--
-- Name: actionlog_actionlog_87f78d4d; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_87f78d4d ON actionlog_actionlog USING btree (content_ad_source_id);


--
-- Name: actionlog_actionlog_a8060d34; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_a8060d34 ON actionlog_actionlog USING btree (ad_group_source_id);


--
-- Name: actionlog_actionlog_action_1d19c831f66c7e23_uniq; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_action_1d19c831f66c7e23_uniq ON actionlog_actionlog USING btree (action);


--
-- Name: actionlog_actionlog_action_type_14332263e7c41daf_uniq; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_action_type_14332263e7c41daf_uniq ON actionlog_actionlog USING btree (action_type);


--
-- Name: actionlog_actionlog_b3da0983; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_b3da0983 ON actionlog_actionlog USING btree (modified_by_id);


--
-- Name: actionlog_actionlog_created_dt_6b1b33fe68819ec6_uniq; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_created_dt_6b1b33fe68819ec6_uniq ON actionlog_actionlog USING btree (created_dt);


--
-- Name: actionlog_actionlog_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_e93cb7eb ON actionlog_actionlog USING btree (created_by_id);


--
-- Name: actionlog_actionlog_id_15546055dcb172b4_idx; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_id_15546055dcb172b4_idx ON actionlog_actionlog USING btree (id, created_dt);


--
-- Name: actionlog_actionlog_modified_dt_2d685bcc84371b18_uniq; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_modified_dt_2d685bcc84371b18_uniq ON actionlog_actionlog USING btree (modified_dt);


--
-- Name: actionlog_actionlog_state_319ee98a8c81bf85_uniq; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX actionlog_actionlog_state_319ee98a8c81bf85_uniq ON actionlog_actionlog USING btree (state);


--
-- Name: auth_group_name_253ae2a6331666e8_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX auth_group_name_253ae2a6331666e8_like ON auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_0e939a4f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX auth_group_permissions_0e939a4f ON auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_8373b171; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX auth_group_permissions_8373b171 ON auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_417f1b1c; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX auth_permission_417f1b1c ON auth_permission USING btree (content_type_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_0b893638; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_0b893638 ON automation_autopilotadgroupsourcebidcpclog USING btree (created_dt);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_22ff94c4 ON automation_autopilotadgroupsourcebidcpclog USING btree (ad_group_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_a8060d34; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_a8060d34 ON automation_autopilotadgroupsourcebidcpclog USING btree (ad_group_source_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_f14acec3 ON automation_autopilotadgroupsourcebidcpclog USING btree (campaign_id);


--
-- Name: automation_campaignbudgetdepletionnotification_0b893638; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_campaignbudgetdepletionnotification_0b893638 ON automation_campaignbudgetdepletionnotification USING btree (created_dt);


--
-- Name: automation_campaignbudgetdepletionnotification_6bc80cbd; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_campaignbudgetdepletionnotification_6bc80cbd ON automation_campaignbudgetdepletionnotification USING btree (account_manager_id);


--
-- Name: automation_campaignbudgetdepletionnotification_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX automation_campaignbudgetdepletionnotification_f14acec3 ON automation_campaignbudgetdepletionnotification USING btree (campaign_id);


--
-- Name: dash_account_b3da0983; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_account_b3da0983 ON dash_account USING btree (modified_by_id);


--
-- Name: dash_account_groups_0e939a4f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_account_groups_0e939a4f ON dash_account_groups USING btree (group_id);


--
-- Name: dash_account_groups_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_account_groups_8a089c2a ON dash_account_groups USING btree (account_id);


--
-- Name: dash_account_name_19b118db2a741bd8_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_account_name_19b118db2a741bd8_like ON dash_account USING btree (name varchar_pattern_ops);


--
-- Name: dash_account_users_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_account_users_8a089c2a ON dash_account_users USING btree (account_id);


--
-- Name: dash_account_users_e8701ad4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_account_users_e8701ad4 ON dash_account_users USING btree (user_id);


--
-- Name: dash_accountsettings_49e3f602; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_accountsettings_49e3f602 ON dash_accountsettings USING btree (default_account_manager_id);


--
-- Name: dash_accountsettings_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_accountsettings_8a089c2a ON dash_accountsettings USING btree (account_id);


--
-- Name: dash_accountsettings_b6c58ed1; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_accountsettings_b6c58ed1 ON dash_accountsettings USING btree (default_sales_representative_id);


--
-- Name: dash_accountsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_accountsettings_e93cb7eb ON dash_accountsettings USING btree (created_by_id);


--
-- Name: dash_adgroup_b3da0983; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroup_b3da0983 ON dash_adgroup USING btree (modified_by_id);


--
-- Name: dash_adgroup_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroup_f14acec3 ON dash_adgroup USING btree (campaign_id);


--
-- Name: dash_adgroupsettings_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsettings_22ff94c4 ON dash_adgroupsettings USING btree (ad_group_id);


--
-- Name: dash_adgroupsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsettings_e93cb7eb ON dash_adgroupsettings USING btree (created_by_id);


--
-- Name: dash_adgroupsource_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsource_0afd9202 ON dash_adgroupsource USING btree (source_id);


--
-- Name: dash_adgroupsource_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsource_22ff94c4 ON dash_adgroupsource USING btree (ad_group_id);


--
-- Name: dash_adgroupsource_709deb08; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsource_709deb08 ON dash_adgroupsource USING btree (source_credentials_id);


--
-- Name: dash_adgroupsourcesettings_a8060d34; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsourcesettings_a8060d34 ON dash_adgroupsourcesettings USING btree (ad_group_source_id);


--
-- Name: dash_adgroupsourcesettings_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsourcesettings_e93cb7eb ON dash_adgroupsourcesettings USING btree (created_by_id);


--
-- Name: dash_adgroupsourcestate_a8060d34; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_adgroupsourcestate_a8060d34 ON dash_adgroupsourcestate USING btree (ad_group_source_id);


--
-- Name: dash_article_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_article_22ff94c4 ON dash_article USING btree (ad_group_id);


--
-- Name: dash_budgethistory_7748a592; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_budgethistory_7748a592 ON dash_budgethistory USING btree (budget_id);


--
-- Name: dash_budgethistory_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_budgethistory_e93cb7eb ON dash_budgethistory USING btree (created_by_id);


--
-- Name: dash_budgetlineitem_5097e6b2; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_budgetlineitem_5097e6b2 ON dash_budgetlineitem USING btree (credit_id);


--
-- Name: dash_budgetlineitem_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_budgetlineitem_e93cb7eb ON dash_budgetlineitem USING btree (created_by_id);


--
-- Name: dash_budgetlineitem_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_budgetlineitem_f14acec3 ON dash_budgetlineitem USING btree (campaign_id);


--
-- Name: dash_campaign_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaign_8a089c2a ON dash_campaign USING btree (account_id);


--
-- Name: dash_campaign_b3da0983; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaign_b3da0983 ON dash_campaign USING btree (modified_by_id);


--
-- Name: dash_campaign_groups_0e939a4f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaign_groups_0e939a4f ON dash_campaign_groups USING btree (group_id);


--
-- Name: dash_campaign_groups_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaign_groups_f14acec3 ON dash_campaign_groups USING btree (campaign_id);


--
-- Name: dash_campaign_users_e8701ad4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaign_users_e8701ad4 ON dash_campaign_users USING btree (user_id);


--
-- Name: dash_campaign_users_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaign_users_f14acec3 ON dash_campaign_users USING btree (campaign_id);


--
-- Name: dash_campaignbudgetsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignbudgetsettings_e93cb7eb ON dash_campaignbudgetsettings USING btree (created_by_id);


--
-- Name: dash_campaignbudgetsettings_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignbudgetsettings_f14acec3 ON dash_campaignbudgetsettings USING btree (campaign_id);


--
-- Name: dash_campaignsettings_3ddf5938; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignsettings_3ddf5938 ON dash_campaignsettings USING btree (sales_representative_id);


--
-- Name: dash_campaignsettings_6bc80cbd; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignsettings_6bc80cbd ON dash_campaignsettings USING btree (account_manager_id);


--
-- Name: dash_campaignsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignsettings_e93cb7eb ON dash_campaignsettings USING btree (created_by_id);


--
-- Name: dash_campaignsettings_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignsettings_f14acec3 ON dash_campaignsettings USING btree (campaign_id);


--
-- Name: dash_campaignsettings_iab_category_15c36af04da422c5_uniq; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_campaignsettings_iab_category_15c36af04da422c5_uniq ON dash_campaignsettings USING btree (iab_category);


--
-- Name: dash_contentad_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_contentad_22ff94c4 ON dash_contentad USING btree (ad_group_id);


--
-- Name: dash_contentad_d4e60137; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_contentad_d4e60137 ON dash_contentad USING btree (batch_id);


--
-- Name: dash_contentadsource_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_contentadsource_0afd9202 ON dash_contentadsource USING btree (source_id);


--
-- Name: dash_contentadsource_abf89b3f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_contentadsource_abf89b3f ON dash_contentadsource USING btree (content_ad_id);


--
-- Name: dash_conversiongoal_ba2eed6c; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_conversiongoal_ba2eed6c ON dash_conversiongoal USING btree (pixel_id);


--
-- Name: dash_conversiongoal_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_conversiongoal_f14acec3 ON dash_conversiongoal USING btree (campaign_id);


--
-- Name: dash_conversionpixel_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_conversionpixel_8a089c2a ON dash_conversionpixel USING btree (account_id);


--
-- Name: dash_credithistory_5097e6b2; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_credithistory_5097e6b2 ON dash_credithistory USING btree (credit_id);


--
-- Name: dash_credithistory_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_credithistory_e93cb7eb ON dash_credithistory USING btree (created_by_id);


--
-- Name: dash_creditlineitem_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_creditlineitem_8a089c2a ON dash_creditlineitem USING btree (account_id);


--
-- Name: dash_creditlineitem_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_creditlineitem_e93cb7eb ON dash_creditlineitem USING btree (created_by_id);


--
-- Name: dash_defaultsourcesettings_9d2c2cd1; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_defaultsourcesettings_9d2c2cd1 ON dash_defaultsourcesettings USING btree (credentials_id);


--
-- Name: dash_exportreport_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_exportreport_22ff94c4 ON dash_exportreport USING btree (ad_group_id);


--
-- Name: dash_exportreport_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_exportreport_8a089c2a ON dash_exportreport USING btree (account_id);


--
-- Name: dash_exportreport_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_exportreport_e93cb7eb ON dash_exportreport USING btree (created_by_id);


--
-- Name: dash_exportreport_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_exportreport_f14acec3 ON dash_exportreport USING btree (campaign_id);


--
-- Name: dash_exportreport_filtered_sources_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_exportreport_filtered_sources_0afd9202 ON dash_exportreport_filtered_sources USING btree (source_id);


--
-- Name: dash_exportreport_filtered_sources_aa7beb1a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_exportreport_filtered_sources_aa7beb1a ON dash_exportreport_filtered_sources USING btree (exportreport_id);


--
-- Name: dash_publisherblacklist_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_publisherblacklist_0afd9202 ON dash_publisherblacklist USING btree (source_id);


--
-- Name: dash_publisherblacklist_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_publisherblacklist_22ff94c4 ON dash_publisherblacklist USING btree (ad_group_id);


--
-- Name: dash_publisherblacklist_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_publisherblacklist_8a089c2a ON dash_publisherblacklist USING btree (account_id);


--
-- Name: dash_publisherblacklist_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_publisherblacklist_f14acec3 ON dash_publisherblacklist USING btree (campaign_id);


--
-- Name: dash_scheduledexportreport_6f78b20c; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_scheduledexportreport_6f78b20c ON dash_scheduledexportreport USING btree (report_id);


--
-- Name: dash_scheduledexportreport_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_scheduledexportreport_e93cb7eb ON dash_scheduledexportreport USING btree (created_by_id);


--
-- Name: dash_scheduledexportreportrecipient_4deefed9; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_scheduledexportreportrecipient_4deefed9 ON dash_scheduledexportreportrecipient USING btree (scheduled_report_id);


--
-- Name: dash_source_ed5cb66b; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_source_ed5cb66b ON dash_source USING btree (source_type_id);


--
-- Name: dash_sourcecredentials_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_sourcecredentials_0afd9202 ON dash_sourcecredentials USING btree (source_id);


--
-- Name: dash_sourcetype_type_7b056ce1a0b025c4_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_sourcetype_type_7b056ce1a0b025c4_like ON dash_sourcetype USING btree (type varchar_pattern_ops);


--
-- Name: dash_useractionlog_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_22ff94c4 ON dash_useractionlog USING btree (ad_group_id);


--
-- Name: dash_useractionlog_83d504ef; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_83d504ef ON dash_useractionlog USING btree (campaign_settings_id);


--
-- Name: dash_useractionlog_8a089c2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_8a089c2a ON dash_useractionlog USING btree (account_id);


--
-- Name: dash_useractionlog_c9776e2a; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_c9776e2a ON dash_useractionlog USING btree (account_settings_id);


--
-- Name: dash_useractionlog_e93cb7eb; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_e93cb7eb ON dash_useractionlog USING btree (created_by_id);


--
-- Name: dash_useractionlog_f14acec3; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_f14acec3 ON dash_useractionlog USING btree (campaign_id);


--
-- Name: dash_useractionlog_f83e08e7; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX dash_useractionlog_f83e08e7 ON dash_useractionlog USING btree (ad_group_settings_id);


--
-- Name: django_admin_log_417f1b1c; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX django_admin_log_417f1b1c ON django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_e8701ad4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX django_admin_log_e8701ad4 ON django_admin_log USING btree (user_id);


--
-- Name: django_session_de54fa62; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX django_session_de54fa62 ON django_session USING btree (expire_date);


--
-- Name: django_session_session_key_461cfeaa630ca218_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX django_session_session_key_461cfeaa630ca218_like ON django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: reports_adgroupgoalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_adgroupgoalconversionstats_0afd9202 ON reports_adgroupgoalconversionstats USING btree (source_id);


--
-- Name: reports_adgroupgoalconversionstats_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_adgroupgoalconversionstats_22ff94c4 ON reports_adgroupgoalconversionstats USING btree (ad_group_id);


--
-- Name: reports_adgroupstats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_adgroupstats_0afd9202 ON reports_adgroupstats USING btree (source_id);


--
-- Name: reports_adgroupstats_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_adgroupstats_22ff94c4 ON reports_adgroupstats USING btree (ad_group_id);


--
-- Name: reports_articlestats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_articlestats_0afd9202 ON reports_articlestats USING btree (source_id);


--
-- Name: reports_articlestats_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_articlestats_22ff94c4 ON reports_articlestats USING btree (ad_group_id);


--
-- Name: reports_articlestats_a00c1b00; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_articlestats_a00c1b00 ON reports_articlestats USING btree (article_id);


--
-- Name: reports_articlestats_ad_group_id_23b66c4e28e5d810_idx; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_articlestats_ad_group_id_23b66c4e28e5d810_idx ON reports_articlestats USING btree (ad_group_id, datetime);


--
-- Name: reports_contentadgoalconversion_goal_type_55f1cce1d23e0872_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadgoalconversion_goal_type_55f1cce1d23e0872_like ON reports_contentadgoalconversionstats USING btree (goal_type varchar_pattern_ops);


--
-- Name: reports_contentadgoalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadgoalconversionstats_0afd9202 ON reports_contentadgoalconversionstats USING btree (source_id);


--
-- Name: reports_contentadgoalconversionstats_197e2321; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadgoalconversionstats_197e2321 ON reports_contentadgoalconversionstats USING btree (goal_type);


--
-- Name: reports_contentadgoalconversionstats_abf89b3f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadgoalconversionstats_abf89b3f ON reports_contentadgoalconversionstats USING btree (content_ad_id);


--
-- Name: reports_contentadpostclickstats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadpostclickstats_0afd9202 ON reports_contentadpostclickstats USING btree (source_id);


--
-- Name: reports_contentadpostclickstats_abf89b3f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadpostclickstats_abf89b3f ON reports_contentadpostclickstats USING btree (content_ad_id);


--
-- Name: reports_contentadstats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadstats_0afd9202 ON reports_contentadstats USING btree (source_id);


--
-- Name: reports_contentadstats_87f78d4d; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadstats_87f78d4d ON reports_contentadstats USING btree (content_ad_source_id);


--
-- Name: reports_contentadstats_abf89b3f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_contentadstats_abf89b3f ON reports_contentadstats USING btree (content_ad_id);


--
-- Name: reports_goalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_goalconversionstats_0afd9202 ON reports_goalconversionstats USING btree (source_id);


--
-- Name: reports_goalconversionstats_22ff94c4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_goalconversionstats_22ff94c4 ON reports_goalconversionstats USING btree (ad_group_id);


--
-- Name: reports_goalconversionstats_a00c1b00; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_goalconversionstats_a00c1b00 ON reports_goalconversionstats USING btree (article_id);


--
-- Name: reports_supplyreportrecipient_0afd9202; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_supplyreportrecipient_0afd9202 ON reports_supplyreportrecipient USING btree (source_id);


--
-- Name: reports_supplyreportrecipient_email_4176c5f708509f21_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX reports_supplyreportrecipient_email_4176c5f708509f21_like ON reports_supplyreportrecipient USING btree (email varchar_pattern_ops);


--
-- Name: zemauth_user_email_660817d9030478bc_like; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX zemauth_user_email_660817d9030478bc_like ON zemauth_user USING btree (email varchar_pattern_ops);


--
-- Name: zemauth_user_email_idx; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user USING btree (lower((email)::text));


--
-- Name: zemauth_user_groups_0e939a4f; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX zemauth_user_groups_0e939a4f ON zemauth_user_groups USING btree (group_id);


--
-- Name: zemauth_user_groups_e8701ad4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX zemauth_user_groups_e8701ad4 ON zemauth_user_groups USING btree (user_id);


--
-- Name: zemauth_user_user_permissions_8373b171; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX zemauth_user_user_permissions_8373b171 ON zemauth_user_user_permissions USING btree (permission_id);


--
-- Name: zemauth_user_user_permissions_e8701ad4; Type: INDEX; Schema: public; Owner: eins; Tablespace:
--

CREATE INDEX zemauth_user_user_permissions_e8701ad4 ON zemauth_user_user_permissions USING btree (user_id);


--
-- Name: D125e6979c26170e2897cb6b9fbf4a40; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT "D125e6979c26170e2897cb6b9fbf4a40" FOREIGN KEY (content_ad_source_id) REFERENCES dash_contentadsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D1f056134358335d812a106bbecb1388; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT "D1f056134358335d812a106bbecb1388" FOREIGN KEY (campaign_settings_id) REFERENCES dash_campaignsettings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D222020c4260fb940f1128384ef4e2a7; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT "D222020c4260fb940f1128384ef4e2a7" FOREIGN KEY (ad_group_settings_id) REFERENCES dash_adgroupsettings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D274f17960266a723e91a879b2938262; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT "D274f17960266a723e91a879b2938262" FOREIGN KEY (account_settings_id) REFERENCES dash_accountsettings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D413a31aad54ed2eab2cb3d0ca1ab26c; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT "D413a31aad54ed2eab2cb3d0ca1ab26c" FOREIGN KEY (content_ad_source_id) REFERENCES dash_contentadsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D4544a30d85cbe2065bcc9b246c9c634; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT "D4544a30d85cbe2065bcc9b246c9c634" FOREIGN KEY (scheduled_report_id) REFERENCES dash_scheduledexportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D91cbf98fff489f9af35a0c541a63e72; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT "D91cbf98fff489f9af35a0c541a63e72" FOREIGN KEY (default_sales_representative_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ac_ad_group_source_id_5e35b3055fbd3996_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT ac_ad_group_source_id_5e35b3055fbd3996_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: action_order_id_5ef59bd83a8712b3_fk_actionlog_actionlogorder_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT action_order_id_5ef59bd83a8712b3_fk_actionlog_actionlogorder_id FOREIGN KEY (order_id) REFERENCES actionlog_actionlogorder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_ac_modified_by_id_7e7800cd3127e10c_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_ac_modified_by_id_7e7800cd3127e10c_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_act_created_by_id_3390c632a986e386_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_act_created_by_id_3390c632a986e386_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ad66818816910836382ffefc141f280b; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT ad66818816910836382ffefc141f280b FOREIGN KEY (source_credentials_id) REFERENCES dash_sourcecredentials(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: au_ad_group_source_id_5fe2bc0149fd4887_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT au_ad_group_source_id_5fe2bc0149fd4887_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_content_type_id_508cf46651277a81_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_content_type_id_508cf46651277a81_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissio_group_id_689710a9a73b7457_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_group_id_689710a9a73b7457_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permission_id_1f49ccbbdc69d2fc_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permission_id_1f49ccbbdc69d2fc_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automati_account_manager_id_5101fb4db2987ac8_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automati_account_manager_id_5101fb4db2987ac8_fk_zemauth_user_id FOREIGN KEY (account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_aut_campaign_id_7870d80a2067c501_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_aut_campaign_id_7870d80a2067c501_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_auto_ad_group_id_29353cf823fae1c4_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_auto_ad_group_id_29353cf823fae1c4_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_cam_campaign_id_6385ff5672ab2818_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_cam_campaign_id_6385ff5672ab2818_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: da_ad_group_source_id_75e25e0c8b4d572d_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT da_ad_group_source_id_75e25e0c8b4d572d_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: da_credentials_id_69620f152a4e171d_fk_dash_sourcecredentials_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT da_credentials_id_69620f152a4e171d_fk_dash_sourcecredentials_id FOREIGN KEY (credentials_id) REFERENCES dash_sourcecredentials(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: das_ad_group_source_id_2bc2e2112081f6e_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsourcestate
    ADD CONSTRAINT das_ad_group_source_id_2bc2e2112081f6e_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: das_sales_representative_id_7a872e15b91b76c3_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT das_sales_representative_id_7a872e15b91b76c3_fk_zemauth_user_id FOREIGN KEY (sales_representative_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_gro_account_id_205f51ea0c4ba450_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_gro_account_id_205f51ea0c4ba450_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_groups_group_id_4631fc181ad52fa_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_group_id_4631fc181ad52fa_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_modified_by_id_3d51056119a59652_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_modified_by_id_3d51056119a59652_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_use_account_id_5e11b94fe9e97351_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_use_account_id_5e11b94fe9e97351_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_users_user_id_511c184c0aeb2754_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_user_id_511c184c0aeb2754_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountse_created_by_id_612e6ccad05f5e3_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountse_created_by_id_612e6ccad05f5e3_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountsett_account_id_3a5781fd9c53d8a1_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsett_account_id_3a5781fd9c53d8a1_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroup_campaign_id_7c0846f18af72a69_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_campaign_id_7c0846f18af72a69_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroup_modified_by_id_6957fb50d67cccf9_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_modified_by_id_6957fb50d67cccf9_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroups_created_by_id_15ce94d078f5a3d2_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroups_created_by_id_15ce94d078f5a3d2_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroups_created_by_id_229d584c2c4eb8cf_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgroups_created_by_id_229d584c2c4eb8cf_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupset_ad_group_id_52bbe2cebc6d3beb_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupset_ad_group_id_52bbe2cebc6d3beb_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsour_ad_group_id_fde095cf19f3715_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsour_ad_group_id_fde095cf19f3715_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsource_source_id_367dc07cd20b0219_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_source_id_367dc07cd20b0219_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_article_ad_group_id_79aa6e718f540dfa_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_ad_group_id_79aa6e718f540dfa_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budge_budget_id_60107fc78fed66a7_fk_dash_budgetlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budge_budget_id_60107fc78fed66a7_fk_dash_budgetlineitem_id FOREIGN KEY (budget_id) REFERENCES dash_budgetlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budge_credit_id_4c0c4719ea6a6609_fk_dash_creditlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budge_credit_id_4c0c4719ea6a6609_fk_dash_creditlineitem_id FOREIGN KEY (credit_id) REFERENCES dash_creditlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgethi_created_by_id_5448d5d41591fb96_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethi_created_by_id_5448d5d41591fb96_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetli_created_by_id_6360c491f729bc2c_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetli_created_by_id_6360c491f729bc2c_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetlin_campaign_id_174e3ffc36d98c50_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlin_campaign_id_174e3ffc36d98c50_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_cam_account_manager_id_362d7afd921ba1e9_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_cam_account_manager_id_362d7afd921ba1e9_fk_zemauth_user_id FOREIGN KEY (account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaig_modified_by_id_741ba1fd28b3509a_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaig_modified_by_id_741ba1fd28b3509a_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign__campaign_id_67477650acd7cd60_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign__campaign_id_67477650acd7cd60_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign__campaign_id_7992ef4e07158559_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign__campaign_id_7992ef4e07158559_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_account_id_46fc75bd4e25459c_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_account_id_46fc75bd4e25459c_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_created_by_id_553e282add87981d_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaign_created_by_id_553e282add87981d_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_created_by_id_5699e985b5c3ea62_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignbudgetsettings
    ADD CONSTRAINT dash_campaign_created_by_id_5699e985b5c3ea62_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_groups_group_id_ad705f42cbaaa7e_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_group_id_ad705f42cbaaa7e_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_users_user_id_540cb488f2a28984_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_user_id_540cb488f2a28984_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaignb_campaign_id_299670a3fe84749a_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignbudgetsettings
    ADD CONSTRAINT dash_campaignb_campaign_id_299670a3fe84749a_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigns_campaign_id_50afcf78e5f21307_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaigns_campaign_id_50afcf78e5f21307_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conten_content_ad_id_39eb0c55cab2148f_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_conten_content_ad_id_39eb0c55cab2148f_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentad_ad_group_id_6fade00c62b7e3ba_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_ad_group_id_6fade00c62b7e3ba_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentad_batch_id_27604bfe91608fc4_fk_dash_uploadbatch_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_batch_id_27604bfe91608fc4_fk_dash_uploadbatch_id FOREIGN KEY (batch_id) REFERENCES dash_uploadbatch(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentadsour_source_id_63078da0e043aaed_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsour_source_id_63078da0e043aaed_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conve_pixel_id_31488bb522a9f7e2_fk_dash_conversionpixel_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conve_pixel_id_31488bb522a9f7e2_fk_dash_conversionpixel_id FOREIGN KEY (pixel_id) REFERENCES dash_conversionpixel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversio_campaign_id_552bc690dfe14873_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversio_campaign_id_552bc690dfe14873_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversionpi_account_id_41a77fbfb3829d5_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpi_account_id_41a77fbfb3829d5_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_credit_credit_id_6b73a9aec988def_fk_dash_creditlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credit_credit_id_6b73a9aec988def_fk_dash_creditlineitem_id FOREIGN KEY (credit_id) REFERENCES dash_creditlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_credithi_created_by_id_667cab4e545ddbee_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithi_created_by_id_667cab4e545ddbee_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditli_created_by_id_6e725d0a4c595130_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditli_created_by_id_6e725d0a4c595130_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditlinei_account_id_13334cb7c84c0fac_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlinei_account_id_13334cb7c84c0fac_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_defaultsource_source_id_318197d72ec0e837_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsource_source_id_318197d72ec0e837_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_demoa_demo_ad_group_id_1380f66b06619d55_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoa_demo_ad_group_id_1380f66b06619d55_fk_dash_adgroup_id FOREIGN KEY (demo_ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_demoa_real_ad_group_id_38bd1d4d2827da1a_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoa_real_ad_group_id_38bd1d4d2827da1a_fk_dash_adgroup_id FOREIGN KEY (real_ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_e_exportreport_id_67cc3959ababbad4_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_e_exportreport_id_67cc3959ababbad4_fk_dash_exportreport_id FOREIGN KEY (exportreport_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportre_created_by_id_100829644781b092_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportre_created_by_id_100829644781b092_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportrepo_ad_group_id_24f2b69d5e01772b_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportrepo_ad_group_id_24f2b69d5e01772b_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportrepo_campaign_id_273cadee8c0072a_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportrepo_campaign_id_273cadee8c0072a_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportrepor_account_id_6b4cc459f095d3fe_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportrepor_account_id_6b4cc459f095d3fe_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport__source_id_429cbee48898cd97_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport__source_id_429cbee48898cd97_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisher_campaign_id_16a8dc1fe68bbc1d_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisher_campaign_id_16a8dc1fe68bbc1d_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherb_ad_group_id_6412ac4e598a7b58_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherb_ad_group_id_6412ac4e598a7b58_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherbla_account_id_c9b1391ae20870b_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherbla_account_id_c9b1391ae20870b_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherblac_source_id_1149cc9d2d63b122_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblac_source_id_1149cc9d2d63b122_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_schedul_report_id_37efeaabd2ffe728_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_schedul_report_id_37efeaabd2ffe728_fk_dash_exportreport_id FOREIGN KEY (report_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_schedule_created_by_id_4991ebc63bf02cf6_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_schedule_created_by_id_4991ebc63bf02cf6_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sour_source_type_id_7ca32910aceeb1c0_fk_dash_sourcetype_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_sour_source_type_id_7ca32910aceeb1c0_fk_dash_sourcetype_id FOREIGN KEY (source_type_id) REFERENCES dash_sourcetype(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sourcecredent_source_id_1c3729cca986d585_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_sourcecredentials
    ADD CONSTRAINT dash_sourcecredent_source_id_1c3729cca986d585_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useractio_campaign_id_1e0d96ec4450dbac_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractio_campaign_id_1e0d96ec4450dbac_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useractio_created_by_id_ff030e12e39bcd0_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractio_created_by_id_ff030e12e39bcd0_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useraction_ad_group_id_4e57f0a40a5bbb49_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useraction_ad_group_id_4e57f0a40a5bbb49_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useractionl_account_id_40e5ee68dafa5dac_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractionl_account_id_40e5ee68dafa5dac_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: default_account_manager_id_271d5867beea1831_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT default_account_manager_id_271d5867beea1831_fk_zemauth_user_id FOREIGN KEY (default_account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: djan_content_type_id_697914295151027a_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT djan_content_type_id_697914295151027a_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_user_id_52fdd58701c5f563_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_52fdd58701c5f563_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroup_ad_group_id_13c4a3d5e20e3c39_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroup_ad_group_id_13c4a3d5e20e3c39_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroup_ad_group_id_2001c33606fdf7b8_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroup_ad_group_id_2001c33606fdf7b8_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupgoa_source_id_7e5f33fc53b57b3d_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoa_source_id_7e5f33fc53b57b3d_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupsta_source_id_1bf5bd45989635ee_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupsta_source_id_1bf5bd45989635ee_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_article_ad_group_id_3769701ff7c08bc2_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_article_ad_group_id_3769701ff7c08bc2_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlest_article_id_7f73111ba61fbcc_fk_dash_article_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlest_article_id_7f73111ba61fbcc_fk_dash_article_id FOREIGN KEY (article_id) REFERENCES dash_article(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlesta_source_id_657629aac3307008_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlesta_source_id_657629aac3307008_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_con_content_ad_id_4bdfb131b60c230a_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_con_content_ad_id_4bdfb131b60c230a_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_con_content_ad_id_67edea839702fc89_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_con_content_ad_id_67edea839702fc89_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_con_content_ad_id_6b72ab957a316bf3_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_con_content_ad_id_6b72ab957a316bf3_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadg_source_id_7a970277294d51f7_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadg_source_id_7a970277294d51f7_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadp_source_id_62765e23e38ee28d_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadp_source_id_62765e23e38ee28d_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentads_source_id_461a985b3e8b6a40_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentads_source_id_461a985b3e8b6a40_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalcon_ad_group_id_2a9a75f4336e4fa8_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalcon_ad_group_id_2a9a75f4336e4fa8_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconv_article_id_2a3e58042a67faca_fk_dash_article_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconv_article_id_2a3e58042a67faca_fk_dash_article_id FOREIGN KEY (article_id) REFERENCES dash_article(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconvers_source_id_70322d4e18d53de_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconvers_source_id_70322d4e18d53de_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_supplyrepor_source_id_a472910927d5af6_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyrepor_source_id_a472910927d5af6_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_internalgrou_group_id_64070c9185256b20_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgrou_group_id_64070c9185256b20_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_us_permission_id_77b59ab3720bfd77_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_us_permission_id_77b59ab3720bfd77_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_groups_group_id_6ba210a4daf39016_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_group_id_6ba210a4daf39016_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_groups_user_id_770269714bafc471_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_user_id_770269714bafc471_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_user_p_user_id_3bd2c96b17985b55_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: eins
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_p_user_id_3bd2c96b17985b55_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

