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
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: actionlog_actionlog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    content_ad_source_id integer,
    created_by_id integer,
    modified_by_id integer,
    order_id integer
);


--
-- Name: actionlog_actionlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE actionlog_actionlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: actionlog_actionlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE actionlog_actionlog_id_seq OWNED BY actionlog_actionlog.id;


--
-- Name: actionlog_actionlogorder; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE actionlog_actionlogorder (
    id integer NOT NULL,
    order_type integer NOT NULL,
    created_dt timestamp with time zone
);


--
-- Name: actionlog_actionlogorder_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE actionlog_actionlogorder_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: actionlog_actionlogorder_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE actionlog_actionlogorder_id_seq OWNED BY actionlog_actionlogorder.id;


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE auth_group (
    id integer NOT NULL,
    name character varying(80) NOT NULL
);


--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE auth_group_id_seq OWNED BY auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE auth_group_permissions_id_seq OWNED BY auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE auth_permission_id_seq OWNED BY auth_permission.id;


--
-- Name: automation_autopilotadgroupsourcebidcpclog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE automation_autopilotadgroupsourcebidcpclog (
    id integer NOT NULL,
    created_dt timestamp with time zone,
    yesterdays_clicks integer,
    yesterdays_spend_cc numeric(10,4),
    previous_cpc_cc numeric(10,4),
    new_cpc_cc numeric(10,4),
    current_daily_budget_cc numeric(10,4),
    comments character varying(1024),
    ad_group_id integer NOT NULL,
    ad_group_source_id integer NOT NULL,
    campaign_id integer NOT NULL
);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE automation_autopilotadgroupsourcebidcpclog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: automation_autopilotadgroupsourcebidcpclog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE automation_autopilotadgroupsourcebidcpclog_id_seq OWNED BY automation_autopilotadgroupsourcebidcpclog.id;


--
-- Name: automation_autopilotlog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE automation_autopilotlog (
    id integer NOT NULL,
    created_dt timestamp with time zone,
    yesterdays_clicks integer,
    yesterdays_spend_cc numeric(10,4),
    previous_cpc_cc numeric(10,4),
    new_cpc_cc numeric(10,4),
    previous_daily_budget numeric(10,4),
    new_daily_budget numeric(10,4),
    budget_comments character varying(1024),
    ad_group_id integer NOT NULL,
    ad_group_source_id integer NOT NULL,
    autopilot_type integer NOT NULL,
    cpc_comments character varying(1024),
    campaign_goal integer
);


--
-- Name: automation_autopilotlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE automation_autopilotlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: automation_autopilotlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE automation_autopilotlog_id_seq OWNED BY automation_autopilotlog.id;


--
-- Name: automation_campaignbudgetdepletionnotification; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE automation_campaignbudgetdepletionnotification (
    id integer NOT NULL,
    created_dt timestamp with time zone,
    available_budget numeric(20,4),
    yesterdays_spend numeric(20,4),
    stopped boolean NOT NULL,
    account_manager_id integer,
    campaign_id integer NOT NULL
);


--
-- Name: automation_campaignbudgetdepletionnotification_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE automation_campaignbudgetdepletionnotification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: automation_campaignbudgetdepletionnotification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE automation_campaignbudgetdepletionnotification_id_seq OWNED BY automation_campaignbudgetdepletionnotification.id;


--
-- Name: convapi_gareportlog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE convapi_gareportlog (
    id integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    for_date date,
    email_subject character varying(1024),
    from_address character varying(1024),
    csv_filename character varying(1024),
    ad_groups character varying(128),
    s3_key character varying(1024),
    visits_reported integer,
    visits_imported integer,
    multimatch integer NOT NULL,
    multimatch_clicks integer NOT NULL,
    nomatch integer NOT NULL,
    state integer NOT NULL,
    errors text,
    recipient character varying(1024)
);


--
-- Name: convapi_gareportlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE convapi_gareportlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: convapi_gareportlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE convapi_gareportlog_id_seq OWNED BY convapi_gareportlog.id;


--
-- Name: convapi_rawgoalconversionstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: convapi_rawgoalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE convapi_rawgoalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: convapi_rawgoalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE convapi_rawgoalconversionstats_id_seq OWNED BY convapi_rawgoalconversionstats.id;


--
-- Name: convapi_rawpostclickstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: convapi_rawpostclickstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE convapi_rawpostclickstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: convapi_rawpostclickstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE convapi_rawpostclickstats_id_seq OWNED BY convapi_rawpostclickstats.id;


--
-- Name: convapi_reportlog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    s3_key character varying(1024),
    state integer NOT NULL,
    errors text,
    recipient character varying(1024)
);


--
-- Name: convapi_reportlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE convapi_reportlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: convapi_reportlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE convapi_reportlog_id_seq OWNED BY convapi_reportlog.id;


--
-- Name: dash_account; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_account (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    outbrain_marketer_id character varying(255),
    modified_by_id integer NOT NULL
);


--
-- Name: dash_account_allowed_sources; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_account_allowed_sources (
    id integer NOT NULL,
    account_id integer NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: dash_account_allowed_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_account_allowed_sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_account_allowed_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_account_allowed_sources_id_seq OWNED BY dash_account_allowed_sources.id;


--
-- Name: dash_account_groups; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_account_groups (
    id integer NOT NULL,
    account_id integer NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: dash_account_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_account_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_account_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_account_groups_id_seq OWNED BY dash_account_groups.id;


--
-- Name: dash_account_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_account_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_account_id_seq OWNED BY dash_account.id;


--
-- Name: dash_account_users; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_account_users (
    id integer NOT NULL,
    account_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: dash_account_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_account_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_account_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_account_users_id_seq OWNED BY dash_account_users.id;


--
-- Name: dash_accountsettings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_accountsettings (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    service_fee numeric(5,4) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    archived boolean NOT NULL,
    changes_text text,
    account_id integer NOT NULL,
    created_by_id integer NOT NULL,
    default_account_manager_id integer,
    default_sales_representative_id integer
);


--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_accountsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_accountsettings_id_seq OWNED BY dash_accountsettings.id;


--
-- Name: dash_adgroup; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_adgroup (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    is_demo boolean NOT NULL,
    content_ads_tab_with_cms boolean NOT NULL,
    campaign_id integer NOT NULL,
    modified_by_id integer NOT NULL
);


--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_adgroup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_adgroup_id_seq OWNED BY dash_adgroup.id;


--
-- Name: dash_adgroupsettings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    enable_ga_tracking boolean NOT NULL,
    enable_adobe_tracking boolean NOT NULL,
    adobe_tracking_param character varying(10) NOT NULL,
    archived boolean NOT NULL,
    display_url character varying(25) NOT NULL,
    brand_name character varying(25) NOT NULL,
    description character varying(140) NOT NULL,
    call_to_action character varying(25) NOT NULL,
    ad_group_name character varying(127) NOT NULL,
    changes_text text,
    ad_group_id integer NOT NULL,
    created_by_id integer,
    ga_tracking_type integer NOT NULL,
    autopilot_daily_budget numeric(10,4),
    autopilot_state integer,
    retargeting_ad_groups text NOT NULL,
    system_user smallint,
    landing_mode boolean NOT NULL,
    CONSTRAINT dash_adgroupsettings_system_user_check CHECK ((system_user >= 0))
);


--
-- Name: dash_adgroupsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_adgroupsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_adgroupsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_adgroupsettings_id_seq OWNED BY dash_adgroupsettings.id;


--
-- Name: dash_adgroupsource; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_adgroupsource (
    id integer NOT NULL,
    source_campaign_key text NOT NULL,
    last_successful_sync_dt timestamp with time zone,
    last_successful_reports_sync_dt timestamp with time zone,
    last_successful_status_sync_dt timestamp with time zone,
    can_manage_content_ads boolean NOT NULL,
    source_content_ad_id character varying(100),
    submission_status integer NOT NULL,
    submission_errors text,
    ad_group_id integer NOT NULL,
    source_id integer NOT NULL,
    source_credentials_id integer
);


--
-- Name: dash_adgroupsource_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_adgroupsource_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_adgroupsource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_adgroupsource_id_seq OWNED BY dash_adgroupsource.id;


--
-- Name: dash_adgroupsourcesettings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_adgroupsourcesettings (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    autopilot_state integer NOT NULL,
    ad_group_source_id integer,
    created_by_id integer,
    landing_mode boolean NOT NULL
);


--
-- Name: dash_adgroupsourcesettings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_adgroupsourcesettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_adgroupsourcesettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_adgroupsourcesettings_id_seq OWNED BY dash_adgroupsourcesettings.id;


--
-- Name: dash_adgroupsourcestate; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_adgroupsourcestate (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    ad_group_source_id integer
);


--
-- Name: dash_adgroupsourcestate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_adgroupsourcestate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_adgroupsourcestate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_adgroupsourcestate_id_seq OWNED BY dash_adgroupsourcestate.id;


--
-- Name: dash_article; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_article (
    id integer NOT NULL,
    url character varying(2048) NOT NULL,
    title character varying(256) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL
);


--
-- Name: dash_article_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_article_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_article_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_article_id_seq OWNED BY dash_article.id;


--
-- Name: dash_budgethistory; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_budgethistory (
    id integer NOT NULL,
    snapshot text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    budget_id integer NOT NULL,
    created_by_id integer
);


--
-- Name: dash_budgethistory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_budgethistory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_budgethistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_budgethistory_id_seq OWNED BY dash_budgethistory.id;


--
-- Name: dash_budgetlineitem; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    credit_id integer NOT NULL,
    freed_cc bigint NOT NULL
);


--
-- Name: dash_budgetlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_budgetlineitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_budgetlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_budgetlineitem_id_seq OWNED BY dash_budgetlineitem.id;


--
-- Name: dash_campaign; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_campaign (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    account_id integer NOT NULL,
    modified_by_id integer
);


--
-- Name: dash_campaign_groups; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_campaign_groups (
    id integer NOT NULL,
    campaign_id integer NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: dash_campaign_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaign_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaign_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaign_groups_id_seq OWNED BY dash_campaign_groups.id;


--
-- Name: dash_campaign_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaign_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaign_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaign_id_seq OWNED BY dash_campaign.id;


--
-- Name: dash_campaign_users; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_campaign_users (
    id integer NOT NULL,
    campaign_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: dash_campaign_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaign_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaign_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaign_users_id_seq OWNED BY dash_campaign_users.id;


--
-- Name: dash_campaignbudgetsettings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: dash_campaignbudgetsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaignbudgetsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaignbudgetsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaignbudgetsettings_id_seq OWNED BY dash_campaignbudgetsettings.id;


--
-- Name: dash_campaigngoal; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_campaigngoal (
    id integer NOT NULL,
    type smallint NOT NULL,
    campaign_id integer NOT NULL,
    created_by_id integer,
    created_dt timestamp with time zone NOT NULL,
    conversion_goal_id integer,
    "primary" boolean NOT NULL,
    CONSTRAINT dash_campaigngoal_type_check CHECK ((type >= 0))
);


--
-- Name: dash_campaigngoal_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaigngoal_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaigngoal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaigngoal_id_seq OWNED BY dash_campaigngoal.id;


--
-- Name: dash_campaigngoalvalue; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_campaigngoalvalue (
    id integer NOT NULL,
    value numeric(15,5) NOT NULL,
    campaign_goal_id integer NOT NULL,
    created_by_id integer,
    created_dt timestamp with time zone NOT NULL
);


--
-- Name: dash_campaigngoalvalue_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaigngoalvalue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaigngoalvalue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaigngoalvalue_id_seq OWNED BY dash_campaigngoalvalue.id;


--
-- Name: dash_campaignsettings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_campaignsettings (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    service_fee numeric(5,4) NOT NULL,
    iab_category character varying(10) NOT NULL,
    promotion_goal integer NOT NULL,
    campaign_goal integer NOT NULL,
    goal_quantity numeric(20,2) NOT NULL,
    target_devices text NOT NULL,
    target_regions text NOT NULL,
    archived boolean NOT NULL,
    changes_text text,
    campaign_id integer NOT NULL,
    created_by_id integer,
    campaign_manager_id integer,
    automatic_campaign_stop boolean NOT NULL,
    landing_mode boolean NOT NULL,
    system_user smallint,
    CONSTRAINT dash_campaignsettings_system_user_check CHECK ((system_user >= 0))
);


--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_campaignsettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_campaignsettings_id_seq OWNED BY dash_campaignsettings.id;


--
-- Name: dash_contentad; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_contentad (
    id integer NOT NULL,
    url character varying(2048) NOT NULL,
    title character varying(256) NOT NULL,
    display_url character varying(25) NOT NULL,
    brand_name character varying(25) NOT NULL,
    description character varying(140) NOT NULL,
    call_to_action character varying(25) NOT NULL,
    image_id character varying(256),
    image_width integer,
    image_height integer,
    image_hash character varying(128),
    crop_areas character varying(128),
    redirect_id character varying(128),
    created_dt timestamp with time zone NOT NULL,
    state integer,
    archived boolean NOT NULL,
    tracker_urls character varying(2048)[],
    ad_group_id integer NOT NULL,
    batch_id integer NOT NULL,
    CONSTRAINT dash_contentad_image_height_check CHECK ((image_height >= 0)),
    CONSTRAINT dash_contentad_image_width_check CHECK ((image_width >= 0))
);


--
-- Name: dash_contentad_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_contentad_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_contentad_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_contentad_id_seq OWNED BY dash_contentad.id;


--
-- Name: dash_contentadsource; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_contentadsource (
    id integer NOT NULL,
    submission_status integer NOT NULL,
    submission_errors text,
    state integer,
    source_state integer,
    source_content_ad_id character varying(50),
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    content_ad_id integer NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: dash_contentadsource_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_contentadsource_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_contentadsource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_contentadsource_id_seq OWNED BY dash_contentadsource.id;


--
-- Name: dash_conversiongoal; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: dash_conversiongoal_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_conversiongoal_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_conversiongoal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_conversiongoal_id_seq OWNED BY dash_conversiongoal.id;


--
-- Name: dash_conversionpixel; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_conversionpixel (
    id integer NOT NULL,
    slug character varying(32) NOT NULL,
    archived boolean NOT NULL,
    last_sync_dt timestamp with time zone,
    created_dt timestamp with time zone NOT NULL,
    account_id integer NOT NULL
);


--
-- Name: dash_conversionpixel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_conversionpixel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_conversionpixel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_conversionpixel_id_seq OWNED BY dash_conversionpixel.id;


--
-- Name: dash_credithistory; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_credithistory (
    id integer NOT NULL,
    snapshot text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    created_by_id integer,
    credit_id integer NOT NULL
);


--
-- Name: dash_credithistory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_credithistory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_credithistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_credithistory_id_seq OWNED BY dash_credithistory.id;


--
-- Name: dash_creditlineitem; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    created_by_id integer,
    flat_fee_cc integer NOT NULL,
    flat_fee_end_date date,
    flat_fee_start_date date
);


--
-- Name: dash_creditlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_creditlineitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_creditlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_creditlineitem_id_seq OWNED BY dash_creditlineitem.id;


--
-- Name: dash_defaultsourcesettings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_defaultsourcesettings (
    id integer NOT NULL,
    params text NOT NULL,
    default_cpc_cc numeric(10,4),
    mobile_cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    credentials_id integer,
    source_id integer NOT NULL
);


--
-- Name: dash_defaultsourcesettings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_defaultsourcesettings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_defaultsourcesettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_defaultsourcesettings_id_seq OWNED BY dash_defaultsourcesettings.id;


--
-- Name: dash_demoadgrouprealadgroup; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_demoadgrouprealadgroup (
    id integer NOT NULL,
    multiplication_factor integer NOT NULL,
    demo_ad_group_id integer NOT NULL,
    real_ad_group_id integer NOT NULL
);


--
-- Name: dash_demoadgrouprealadgroup_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_demoadgrouprealadgroup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_demoadgrouprealadgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_demoadgrouprealadgroup_id_seq OWNED BY dash_demoadgrouprealadgroup.id;


--
-- Name: dash_exportreport; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    created_by_id integer NOT NULL,
    include_model_ids boolean NOT NULL
);


--
-- Name: dash_exportreport_filtered_sources; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_exportreport_filtered_sources (
    id integer NOT NULL,
    exportreport_id integer NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: dash_exportreport_filtered_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_exportreport_filtered_sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_exportreport_filtered_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_exportreport_filtered_sources_id_seq OWNED BY dash_exportreport_filtered_sources.id;


--
-- Name: dash_exportreport_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_exportreport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_exportreport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_exportreport_id_seq OWNED BY dash_exportreport.id;


--
-- Name: dash_gaanalyticsaccount; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_gaanalyticsaccount (
    id integer NOT NULL,
    ga_account_id character varying(127) NOT NULL,
    ga_web_property_id character varying(127) NOT NULL,
    account_id integer NOT NULL
);


--
-- Name: dash_gaanalyticsaccount_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_gaanalyticsaccount_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_gaanalyticsaccount_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_gaanalyticsaccount_id_seq OWNED BY dash_gaanalyticsaccount.id;


--
-- Name: dash_outbrainaccount; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_outbrainaccount (
    id integer NOT NULL,
    marketer_id character varying(255) NOT NULL,
    used boolean NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    marketer_name character varying(255)
);


--
-- Name: dash_outbrainaccount_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_outbrainaccount_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_outbrainaccount_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_outbrainaccount_id_seq OWNED BY dash_outbrainaccount.id;


--
-- Name: dash_publisherblacklist; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_publisherblacklist (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    everywhere boolean NOT NULL,
    status integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    account_id integer,
    ad_group_id integer,
    campaign_id integer,
    source_id integer,
    external_id character varying(127)
);


--
-- Name: dash_publisherblacklist_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_publisherblacklist_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_publisherblacklist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_publisherblacklist_id_seq OWNED BY dash_publisherblacklist.id;


--
-- Name: dash_scheduledexportreport; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: dash_scheduledexportreport_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_scheduledexportreport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_scheduledexportreport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_scheduledexportreport_id_seq OWNED BY dash_scheduledexportreport.id;


--
-- Name: dash_scheduledexportreportlog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_scheduledexportreportlog (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    start_date date,
    end_date date,
    report_filename character varying(1024),
    recipient_emails character varying(1024),
    state integer NOT NULL,
    errors text,
    scheduled_report_id integer NOT NULL
);


--
-- Name: dash_scheduledexportreportlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_scheduledexportreportlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_scheduledexportreportlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_scheduledexportreportlog_id_seq OWNED BY dash_scheduledexportreportlog.id;


--
-- Name: dash_scheduledexportreportrecipient; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_scheduledexportreportrecipient (
    id integer NOT NULL,
    email character varying(254) NOT NULL,
    scheduled_report_id integer NOT NULL
);


--
-- Name: dash_scheduledexportreportrecipient_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_scheduledexportreportrecipient_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_scheduledexportreportrecipient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_scheduledexportreportrecipient_id_seq OWNED BY dash_scheduledexportreportrecipient.id;


--
-- Name: dash_source; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_source (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    tracking_slug character varying(50) NOT NULL,
    bidder_slug character varying(50),
    maintenance boolean NOT NULL,
    deprecated boolean NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    released boolean NOT NULL,
    content_ad_submission_type integer NOT NULL,
    source_type_id integer,
    supports_retargeting boolean NOT NULL,
    supports_retargeting_manually boolean NOT NULL,
    default_cpc_cc numeric(10,4) NOT NULL,
    default_daily_budget_cc numeric(10,4) NOT NULL,
    default_mobile_cpc_cc numeric(10,4) NOT NULL
);


--
-- Name: dash_source_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_source_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_source_id_seq OWNED BY dash_source.id;


--
-- Name: dash_sourcecredentials; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_sourcecredentials (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    credentials text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: dash_sourcecredentials_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_sourcecredentials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_sourcecredentials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_sourcecredentials_id_seq OWNED BY dash_sourcecredentials.id;


--
-- Name: dash_sourcetype; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_sourcetype (
    id integer NOT NULL,
    type character varying(127) NOT NULL,
    available_actions smallint[],
    min_cpc numeric(10,4),
    min_daily_budget numeric(10,4),
    max_cpc numeric(10,4),
    max_daily_budget numeric(10,4),
    cpc_decimal_places smallint,
    delete_traffic_metrics_threshold integer NOT NULL,
    budgets_tz character varying(63) NOT NULL,
    CONSTRAINT dash_sourcetype_cpc_decimal_places_check CHECK ((cpc_decimal_places >= 0))
);


--
-- Name: dash_sourcetype_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_sourcetype_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_sourcetype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_sourcetype_id_seq OWNED BY dash_sourcetype.id;


--
-- Name: dash_uploadbatch; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dash_uploadbatch (
    id integer NOT NULL,
    name character varying(1024) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    status integer NOT NULL,
    error_report_key character varying(1024),
    num_errors integer,
    processed_content_ads integer,
    inserted_content_ads integer,
    batch_size integer,
    cancelled boolean NOT NULL,
    propagated_content_ads integer,
    CONSTRAINT dash_uploadbatch_batch_size_check CHECK ((batch_size >= 0)),
    CONSTRAINT dash_uploadbatch_inserted_content_ads_check CHECK ((inserted_content_ads >= 0)),
    CONSTRAINT dash_uploadbatch_num_errors_check CHECK ((num_errors >= 0)),
    CONSTRAINT dash_uploadbatch_processed_content_ads_check CHECK ((processed_content_ads >= 0)),
    CONSTRAINT dash_uploadbatch_propagated_content_ads_check CHECK ((propagated_content_ads >= 0))
);


--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_uploadbatch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_uploadbatch_id_seq OWNED BY dash_uploadbatch.id;


--
-- Name: dash_useractionlog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: dash_useractionlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_useractionlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_useractionlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_useractionlog_id_seq OWNED BY dash_useractionlog.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE django_admin_log_id_seq OWNED BY django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE django_migrations_id_seq OWNED BY django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


--
-- Name: reports_adgroupgoalconversionstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: reports_adgroupgoalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_adgroupgoalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_adgroupgoalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_adgroupgoalconversionstats_id_seq OWNED BY reports_adgroupgoalconversionstats.id;


--
-- Name: reports_adgroupstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE reports_adgroupstats (
    id integer NOT NULL,
    impressions integer NOT NULL,
    clicks integer NOT NULL,
    cost_cc integer NOT NULL,
    data_cost_cc integer NOT NULL,
    visits integer NOT NULL,
    new_visits integer NOT NULL,
    bounced_visits integer NOT NULL,
    pageviews integer NOT NULL,
    duration integer NOT NULL,
    has_traffic_metrics integer NOT NULL,
    has_postclick_metrics integer NOT NULL,
    has_conversion_metrics integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: reports_adgroupstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_adgroupstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_adgroupstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_adgroupstats_id_seq OWNED BY reports_adgroupstats.id;


--
-- Name: reports_articlestats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE reports_articlestats (
    id integer NOT NULL,
    impressions integer NOT NULL,
    clicks integer NOT NULL,
    cost_cc integer NOT NULL,
    data_cost_cc integer NOT NULL,
    visits integer NOT NULL,
    new_visits integer NOT NULL,
    bounced_visits integer NOT NULL,
    pageviews integer NOT NULL,
    duration integer NOT NULL,
    has_traffic_metrics integer NOT NULL,
    has_postclick_metrics integer NOT NULL,
    has_conversion_metrics integer NOT NULL,
    datetime timestamp with time zone NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    article_id integer NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: reports_articlestats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_articlestats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_articlestats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_articlestats_id_seq OWNED BY reports_articlestats.id;


--
-- Name: reports_budgetdailystatement; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE reports_budgetdailystatement (
    id integer NOT NULL,
    date date NOT NULL,
    media_spend_nano bigint NOT NULL,
    data_spend_nano bigint NOT NULL,
    license_fee_nano bigint NOT NULL,
    budget_id integer NOT NULL
);


--
-- Name: reports_budgetdailystatement_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_budgetdailystatement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_budgetdailystatement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_budgetdailystatement_id_seq OWNED BY reports_budgetdailystatement.id;


--
-- Name: reports_contentadgoalconversionstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE reports_contentadgoalconversionstats (
    id integer NOT NULL,
    date timestamp with time zone NOT NULL,
    goal_type character varying(15) NOT NULL,
    goal_name character varying(256) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    conversions integer,
    content_ad_id integer NOT NULL,
    source_id integer NOT NULL
);


--
-- Name: reports_contentadgoalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_contentadgoalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_contentadgoalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_contentadgoalconversionstats_id_seq OWNED BY reports_contentadgoalconversionstats.id;


--
-- Name: reports_contentadpostclickstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: reports_contentadpostclickstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_contentadpostclickstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_contentadpostclickstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_contentadpostclickstats_id_seq OWNED BY reports_contentadpostclickstats.id;


--
-- Name: reports_contentadstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: reports_contentadstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_contentadstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_contentadstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_contentadstats_id_seq OWNED BY reports_contentadstats.id;


--
-- Name: reports_goalconversionstats; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: reports_goalconversionstats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_goalconversionstats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_goalconversionstats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_goalconversionstats_id_seq OWNED BY reports_goalconversionstats.id;


--
-- Name: reports_supplyreportrecipient; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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


--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_supplyreportrecipient_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_supplyreportrecipient_id_seq OWNED BY reports_supplyreportrecipient.id;


--
-- Name: zemauth_internalgroup; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE zemauth_internalgroup (
    id integer NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: zemauth_internalgroup_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE zemauth_internalgroup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: zemauth_internalgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE zemauth_internalgroup_id_seq OWNED BY zemauth_internalgroup.id;


--
-- Name: zemauth_user; Type: TABLE; Schema: public; Owner: -; Tablespace: 
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
    show_onboarding_guidance boolean NOT NULL,
    is_test_user boolean NOT NULL
);


--
-- Name: zemauth_user_groups; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE zemauth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: zemauth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE zemauth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: zemauth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE zemauth_user_groups_id_seq OWNED BY zemauth_user_groups.id;


--
-- Name: zemauth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE zemauth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: zemauth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE zemauth_user_id_seq OWNED BY zemauth_user.id;


--
-- Name: zemauth_user_user_permissions; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE zemauth_user_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: zemauth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE zemauth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: zemauth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE zemauth_user_user_permissions_id_seq OWNED BY zemauth_user_user_permissions.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog ALTER COLUMN id SET DEFAULT nextval('actionlog_actionlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlogorder ALTER COLUMN id SET DEFAULT nextval('actionlog_actionlogorder_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group ALTER COLUMN id SET DEFAULT nextval('auth_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('auth_group_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog ALTER COLUMN id SET DEFAULT nextval('automation_autopilotadgroupsourcebidcpclog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog ALTER COLUMN id SET DEFAULT nextval('automation_autopilotlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification ALTER COLUMN id SET DEFAULT nextval('automation_campaignbudgetdepletionnotification_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY convapi_gareportlog ALTER COLUMN id SET DEFAULT nextval('convapi_gareportlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY convapi_rawgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('convapi_rawgoalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY convapi_rawpostclickstats ALTER COLUMN id SET DEFAULT nextval('convapi_rawpostclickstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY convapi_reportlog ALTER COLUMN id SET DEFAULT nextval('convapi_reportlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account ALTER COLUMN id SET DEFAULT nextval('dash_account_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources ALTER COLUMN id SET DEFAULT nextval('dash_account_allowed_sources_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups ALTER COLUMN id SET DEFAULT nextval('dash_account_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users ALTER COLUMN id SET DEFAULT nextval('dash_account_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings ALTER COLUMN id SET DEFAULT nextval('dash_accountsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup ALTER COLUMN id SET DEFAULT nextval('dash_adgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsource_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsourcesettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcestate ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsourcestate_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_article ALTER COLUMN id SET DEFAULT nextval('dash_article_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory ALTER COLUMN id SET DEFAULT nextval('dash_budgethistory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem ALTER COLUMN id SET DEFAULT nextval('dash_budgetlineitem_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign ALTER COLUMN id SET DEFAULT nextval('dash_campaign_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups ALTER COLUMN id SET DEFAULT nextval('dash_campaign_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users ALTER COLUMN id SET DEFAULT nextval('dash_campaign_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignbudgetsettings ALTER COLUMN id SET DEFAULT nextval('dash_campaignbudgetsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal ALTER COLUMN id SET DEFAULT nextval('dash_campaigngoal_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue ALTER COLUMN id SET DEFAULT nextval('dash_campaigngoalvalue_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings ALTER COLUMN id SET DEFAULT nextval('dash_campaignsettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad ALTER COLUMN id SET DEFAULT nextval('dash_contentad_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource ALTER COLUMN id SET DEFAULT nextval('dash_contentadsource_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal ALTER COLUMN id SET DEFAULT nextval('dash_conversiongoal_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversionpixel ALTER COLUMN id SET DEFAULT nextval('dash_conversionpixel_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory ALTER COLUMN id SET DEFAULT nextval('dash_credithistory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem ALTER COLUMN id SET DEFAULT nextval('dash_creditlineitem_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings ALTER COLUMN id SET DEFAULT nextval('dash_defaultsourcesettings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup ALTER COLUMN id SET DEFAULT nextval('dash_demoadgrouprealadgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_filtered_sources_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_gaanalyticsaccount ALTER COLUMN id SET DEFAULT nextval('dash_gaanalyticsaccount_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_outbrainaccount ALTER COLUMN id SET DEFAULT nextval('dash_outbrainaccount_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist ALTER COLUMN id SET DEFAULT nextval('dash_publisherblacklist_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreport_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportlog ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreportlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreportrecipient_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source ALTER COLUMN id SET DEFAULT nextval('dash_source_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcecredentials ALTER COLUMN id SET DEFAULT nextval('dash_sourcecredentials_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetype ALTER COLUMN id SET DEFAULT nextval('dash_sourcetype_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_uploadbatch ALTER COLUMN id SET DEFAULT nextval('dash_uploadbatch_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog ALTER COLUMN id SET DEFAULT nextval('dash_useractionlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_adgroupgoalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats ALTER COLUMN id SET DEFAULT nextval('reports_adgroupstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats ALTER COLUMN id SET DEFAULT nextval('reports_articlestats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatement ALTER COLUMN id SET DEFAULT nextval('reports_budgetdailystatement_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadgoalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadpostclickstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_goalconversionstats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_supplyreportrecipient ALTER COLUMN id SET DEFAULT nextval('reports_supplyreportrecipient_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_internalgroup ALTER COLUMN id SET DEFAULT nextval('zemauth_internalgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user ALTER COLUMN id SET DEFAULT nextval('zemauth_user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups ALTER COLUMN id SET DEFAULT nextval('zemauth_user_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('zemauth_user_user_permissions_id_seq'::regclass);


--
-- Data for Name: actionlog_actionlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY actionlog_actionlog (id, action, state, action_type, message, payload, expiration_dt, created_dt, modified_dt, ad_group_source_id, content_ad_source_id, created_by_id, modified_by_id, order_id) FROM stdin;
\.


--
-- Name: actionlog_actionlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('actionlog_actionlog_id_seq', 1, false);


--
-- Data for Name: actionlog_actionlogorder; Type: TABLE DATA; Schema: public; Owner: -
--

COPY actionlog_actionlogorder (id, order_type, created_dt) FROM stdin;
\.


--
-- Name: actionlog_actionlogorder_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('actionlog_actionlogorder_id_seq', 1, false);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY auth_group (id, name) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('auth_group_id_seq', 1, false);


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', 1, false);


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
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
32	Can add campaign goal	11	add_campaigngoal
33	Can change campaign goal	11	change_campaigngoal
34	Can delete campaign goal	11	delete_campaigngoal
35	Can add campaign goal value	12	add_campaigngoalvalue
36	Can change campaign goal value	12	change_campaigngoalvalue
37	Can delete campaign goal value	12	delete_campaigngoalvalue
38	Can add Source Type	13	add_sourcetype
39	Can change Source Type	13	change_sourcetype
40	Can delete Source Type	13	delete_sourcetype
41	Can add source	14	add_source
42	Can change source	14	change_source
43	Can delete source	14	delete_source
44	Can add source credentials	15	add_sourcecredentials
45	Can change source credentials	15	change_sourcecredentials
46	Can delete source credentials	15	delete_sourcecredentials
47	Can add default source settings	16	add_defaultsourcesettings
48	Can change default source settings	16	change_defaultsourcesettings
49	Can delete default source settings	16	delete_defaultsourcesettings
50	Can add ad group	17	add_adgroup
51	Can change ad group	17	change_adgroup
52	Can delete ad group	17	delete_adgroup
53	Can add ad group source	18	add_adgroupsource
54	Can change ad group source	18	change_adgroupsource
55	Can delete ad group source	18	delete_adgroupsource
56	Can add ad group settings	19	add_adgroupsettings
57	Can change ad group settings	19	change_adgroupsettings
58	Can delete ad group settings	19	delete_adgroupsettings
59	Can view settings in dashboard.	19	settings_view
60	Can add ad group source state	20	add_adgroupsourcestate
61	Can change ad group source state	20	change_adgroupsourcestate
62	Can delete ad group source state	20	delete_adgroupsourcestate
63	Can add ad group source settings	21	add_adgroupsourcesettings
64	Can change ad group source settings	21	change_adgroupsourcesettings
65	Can delete ad group source settings	21	delete_adgroupsourcesettings
66	Can add upload batch	22	add_uploadbatch
67	Can change upload batch	22	change_uploadbatch
68	Can delete upload batch	22	delete_uploadbatch
69	Can add content ad	23	add_contentad
70	Can change content ad	23	change_contentad
71	Can delete content ad	23	delete_contentad
72	Can add content ad source	24	add_contentadsource
73	Can change content ad source	24	change_contentadsource
74	Can delete content ad source	24	delete_contentadsource
75	Can add article	25	add_article
76	Can change article	25	change_article
77	Can delete article	25	delete_article
78	Can add campaign budget settings	26	add_campaignbudgetsettings
79	Can change campaign budget settings	26	change_campaignbudgetsettings
80	Can delete campaign budget settings	26	delete_campaignbudgetsettings
81	Can add conversion pixel	27	add_conversionpixel
82	Can change conversion pixel	27	change_conversionpixel
83	Can delete conversion pixel	27	delete_conversionpixel
84	Can add conversion goal	28	add_conversiongoal
85	Can change conversion goal	28	change_conversiongoal
86	Can delete conversion goal	28	delete_conversiongoal
87	Can add demo ad group real ad group	29	add_demoadgrouprealadgroup
88	Can change demo ad group real ad group	29	change_demoadgrouprealadgroup
89	Can delete demo ad group real ad group	29	delete_demoadgrouprealadgroup
90	Can add user action log	30	add_useractionlog
91	Can change user action log	30	change_useractionlog
92	Can delete user action log	30	delete_useractionlog
93	Can add publisher blacklist	31	add_publisherblacklist
94	Can change publisher blacklist	31	change_publisherblacklist
95	Can delete publisher blacklist	31	delete_publisherblacklist
96	Can add credit line item	32	add_creditlineitem
97	Can change credit line item	32	change_creditlineitem
98	Can delete credit line item	32	delete_creditlineitem
99	Can add budget line item	33	add_budgetlineitem
100	Can change budget line item	33	change_budgetlineitem
101	Can delete budget line item	33	delete_budgetlineitem
102	Can add credit history	34	add_credithistory
103	Can change credit history	34	change_credithistory
104	Can delete credit history	34	delete_credithistory
105	Can add budget history	35	add_budgethistory
106	Can change budget history	35	change_budgethistory
107	Can delete budget history	35	delete_budgethistory
108	Can add export report	36	add_exportreport
109	Can change export report	36	change_exportreport
110	Can delete export report	36	delete_exportreport
111	Can add scheduled export report	37	add_scheduledexportreport
112	Can change scheduled export report	37	change_scheduledexportreport
113	Can delete scheduled export report	37	delete_scheduledexportreport
114	Can add scheduled export report recipient	38	add_scheduledexportreportrecipient
115	Can change scheduled export report recipient	38	change_scheduledexportreportrecipient
116	Can delete scheduled export report recipient	38	delete_scheduledexportreportrecipient
117	Can add scheduled export report log	39	add_scheduledexportreportlog
118	Can change scheduled export report log	39	change_scheduledexportreportlog
119	Can delete scheduled export report log	39	delete_scheduledexportreportlog
120	Can add ga analytics account	40	add_gaanalyticsaccount
121	Can change ga analytics account	40	change_gaanalyticsaccount
122	Can delete ga analytics account	40	delete_gaanalyticsaccount
123	Can add user	41	add_user
124	Can change user	41	change_user
125	Can delete user	41	delete_user
126	Can view campaign's settings tab.	41	campaign_settings_view
127	Can view campaign's agency tab.	41	campaign_agency_view
128	Can view campaign's ad groups tab in dashboard.	41	campaign_ad_groups_view
129	Can view campaign's budget tab.	41	campaign_budget_view
130	Can be chosen as account manager.	41	campaign_settings_account_manager
131	Can be chosen as sales representative.	41	campaign_settings_sales_rep
132	Can view supply dash link.	41	supply_dash_link_view
133	Can view ad group's agency tab.	41	ad_group_agency_tab_view
134	Can view all accounts's accounts tab.	41	all_accounts_accounts_view
135	Can view accounts's campaigns tab.	41	account_campaigns_view
136	Can view accounts's agency tab.	41	account_agency_view
137	Can view accounts's credit tab.	41	account_credit_view
138	Can add media sources.	41	ad_group_sources_add_source
139	Can view campaign sources view.	41	campaign_sources_view
140	Can view account sources view.	41	account_sources_view
141	Can view all accounts sources view.	41	all_accounts_sources_view
142	Can add ad groups.	41	campaign_ad_groups_add_ad_group
143	Can add campaigns.	41	account_campaigns_add_campaign
144	Can add accounts.	41	all_accounts_accounts_add_account
145	Can see new sidebar.	41	all_new_sidebar
146	Can do campaign budget management.	41	campaign_budget_management_view
147	Can view account budget.	41	account_budget_view
148	Can view all accounts budget.	41	all_accounts_budget_view
149	Can archive or restore an entity.	41	archive_restore_entity
150	Can view archived entities.	41	view_archived_entities
151	Can view unspent budget.	41	unspent_budget_view
152	Can switch to demo mode.	41	switch_to_demo_mode
153	Can view and set account access permissions.	41	account_agency_access_permissions
154	New users are added to this group.	41	group_new_user_add
155	Can set per-source settings.	41	set_ad_group_source_settings
156	Can see current per-source state.	41	see_current_ad_group_source_state
157	Can download detailed report on campaign level.	41	campaign_ad_groups_detailed_report
158	Can view content ads postclick acq. metrics.	41	content_ads_postclick_acquisition
159	Can view content ads postclick eng. metrics.	41	content_ads_postclick_engagement
160	Can view aggregate postclick acq. metrics.	41	aggregate_postclick_acquisition
161	Can view aggregate postclick eng. metrics.	41	aggregate_postclick_engagement
162	Can view publishers conversion goals.	41	view_pubs_conversion_goals
163	Can view publishers postclick stats.	41	view_pubs_postclick_stats
164	Can see data status column in table.	41	data_status_column
165	Can view new content ads tab.	41	new_content_ads_tab
166	Can filter sources	41	filter_sources
167	Can upload new content ads.	41	upload_content_ads
168	Can set status of content ads.	41	set_content_ad_status
169	Can download bulk content ad csv.	41	get_content_ad_csv
170	Can view and use bulk content ads actions.	41	content_ads_bulk_actions
171	Can toggle Google Analytics performance tracking.	41	can_toggle_ga_performance_tracking
172	Can toggle Adobe Analytics performance tracking.	41	can_toggle_adobe_performance_tracking
173	Can see media source status on submission status popover	41	can_see_media_source_status_on_submission_popover
174	Can set subdivision targeting	41	can_set_subdivision_targeting
175	Can set media source to auto-pilot	41	can_set_media_source_to_auto_pilot
176	Can manage conversion pixels	41	manage_conversion_pixels
177	Automatically add media sources on ad group creation	41	add_media_sources_automatically
178	Can see intercom widget	41	has_intercom
179	Can see publishers	41	can_see_publishers
180	Can manage conversion goals on campaign level	41	manage_conversion_goals
181	Can see Redshift postclick statistics	41	can_see_redshift_postclick_statistics
182	Automatic campaign stop on depleted budget applies to campaigns in this group	41	group_campaign_stop_on_budget_depleted
183	Can see publishers blacklist status	41	can_see_publisher_blacklist_status
184	Can modify publishers blacklist status	41	can_modify_publisher_blacklist_status
185	Can see conversions and goals in reports	41	conversion_reports
186	Can download reports using new export facilities	41	exports_plus
187	Can modify allowed sources on account level	41	can_modify_allowed_sources
188	Can view ad group settings defaults on campaign level	41	settings_defaults_on_campaign_level
189	Can view or modify global publishers blacklist status	41	can_access_global_publisher_blacklist_status
190	Can view or modify account and campaign publishers blacklist status	41	can_access_campaign_account_publisher_blacklist_status
191	Can see all available media sources in account settings	41	can_see_all_available_sources
192	Can see info box	41	can_see_infobox
193	Can view account's Account tab.	41	account_account_view
194	Can view effective costs	41	can_view_effective_costs
195	Can view actual costs	41	can_view_actual_costs
196	Can modify Outbrain account publisher blacklist status	41	can_modify_outbrain_account_publisher_blacklist_status
197	Can set Ad Group to Auto-Pilot (budget and CPC automation)	41	can_set_adgroup_to_auto_pilot
198	Can set ad group max cpc	41	can_set_ad_group_max_cpc
199	Can view retargeting settings	41	can_view_retargeting_settings
200	Can view flat fees in All accounts/accounts table	41	can_view_flat_fees
201	Can control ad group state in Campaign / Ad Groups table	41	can_control_ad_group_state_in_table
202	Can see and manage campaign goals	41	can_see_campaign_goals
203	Can see projections	41	can_see_projections
204	Can see Account Manager and Sales Representative in accounts table.	41	can_see_managers_in_accounts_table
205	Can see Campaign Manager in campaigns table.	41	can_see_managers_in_campaigns_table
206	Can show or hide chart	41	can_hide_chart
207	Can access info box on adgroup level	41	can_access_ad_group_infobox
208	Can access info box on campaign level	41	can_access_campaign_infobox
209	Can access info box on account level	41	can_access_account_infobox
210	Can access info box on all accounts level	41	can_access_all_accounts_infobox
211	Can view aggregate campaign goal optimisation metrics	41	campaign_goal_optimization
212	Can view goal performance information	41	campaign_goal_performance
213	Can include model ids in reports	41	can_include_model_ids_in_reports
214	Can add internal group	42	add_internalgroup
215	Can change internal group	42	change_internalgroup
216	Can delete internal group	42	delete_internalgroup
217	Can add action log order	43	add_actionlogorder
218	Can change action log order	43	change_actionlogorder
219	Can delete action log order	43	delete_actionlogorder
220	Can add action log	44	add_actionlog
221	Can change action log	44	change_actionlog
222	Can delete action log	44	delete_actionlog
223	Can view manual ActionLog actions	44	manual_view
224	Can acknowledge manual ActionLog actions	44	manual_acknowledge
225	Can add article stats	45	add_articlestats
226	Can change article stats	45	change_articlestats
227	Can delete article stats	45	delete_articlestats
228	Can add goal conversion stats	46	add_goalconversionstats
229	Can change goal conversion stats	46	change_goalconversionstats
230	Can delete goal conversion stats	46	delete_goalconversionstats
231	Can add ad group stats	47	add_adgroupstats
232	Can change ad group stats	47	change_adgroupstats
233	Can delete ad group stats	47	delete_adgroupstats
234	Can add ad group goal conversion stats	48	add_adgroupgoalconversionstats
235	Can change ad group goal conversion stats	48	change_adgroupgoalconversionstats
236	Can delete ad group goal conversion stats	48	delete_adgroupgoalconversionstats
237	Can add content ad stats	49	add_contentadstats
238	Can change content ad stats	49	change_contentadstats
239	Can delete content ad stats	49	delete_contentadstats
240	Can add supply report recipient	50	add_supplyreportrecipient
241	Can change supply report recipient	50	change_supplyreportrecipient
242	Can delete supply report recipient	50	delete_supplyreportrecipient
243	Can add content ad postclick stats	51	add_contentadpostclickstats
244	Can change content ad postclick stats	51	change_contentadpostclickstats
245	Can delete content ad postclick stats	51	delete_contentadpostclickstats
246	Can add content ad goal conversion stats	52	add_contentadgoalconversionstats
247	Can change content ad goal conversion stats	52	change_contentadgoalconversionstats
248	Can delete content ad goal conversion stats	52	delete_contentadgoalconversionstats
249	Can add budget daily statement	53	add_budgetdailystatement
250	Can change budget daily statement	53	change_budgetdailystatement
251	Can delete budget daily statement	53	delete_budgetdailystatement
252	Can add raw postclick stats	54	add_rawpostclickstats
253	Can change raw postclick stats	54	change_rawpostclickstats
254	Can delete raw postclick stats	54	delete_rawpostclickstats
255	Can add raw goal conversion stats	55	add_rawgoalconversionstats
256	Can change raw goal conversion stats	55	change_rawgoalconversionstats
257	Can delete raw goal conversion stats	55	delete_rawgoalconversionstats
258	Can add ga report log	56	add_gareportlog
259	Can change ga report log	56	change_gareportlog
260	Can delete ga report log	56	delete_gareportlog
261	Can add report log	57	add_reportlog
262	Can change report log	57	change_reportlog
263	Can delete report log	57	delete_reportlog
264	Can add campaign budget depletion notification	58	add_campaignbudgetdepletionnotification
265	Can change campaign budget depletion notification	58	change_campaignbudgetdepletionnotification
266	Can delete campaign budget depletion notification	58	delete_campaignbudgetdepletionnotification
267	Can add autopilot ad group source bid cpc log	59	add_autopilotadgroupsourcebidcpclog
268	Can change autopilot ad group source bid cpc log	59	change_autopilotadgroupsourcebidcpclog
269	Can delete autopilot ad group source bid cpc log	59	delete_autopilotadgroupsourcebidcpclog
270	Can add autopilot log	60	add_autopilotlog
271	Can change autopilot log	60	change_autopilotlog
272	Can delete autopilot log	60	delete_autopilotlog
273	Can view publishers postclick acq. metrics.	41	view_pubs_postclick_acquisition
274	Can view publishers postclick eng. metrics.	41	view_pubs_postclick_engagement
275	Has Drift snippet	41	has_drift
276	Has Supporthero snippet	41	has_supporthero
\.


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('auth_permission_id_seq', 276, true);


--
-- Data for Name: automation_autopilotadgroupsourcebidcpclog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY automation_autopilotadgroupsourcebidcpclog (id, created_dt, yesterdays_clicks, yesterdays_spend_cc, previous_cpc_cc, new_cpc_cc, current_daily_budget_cc, comments, ad_group_id, ad_group_source_id, campaign_id) FROM stdin;
\.


--
-- Name: automation_autopilotadgroupsourcebidcpclog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('automation_autopilotadgroupsourcebidcpclog_id_seq', 1, false);


--
-- Data for Name: automation_autopilotlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY automation_autopilotlog (id, created_dt, yesterdays_clicks, yesterdays_spend_cc, previous_cpc_cc, new_cpc_cc, previous_daily_budget, new_daily_budget, budget_comments, ad_group_id, ad_group_source_id, autopilot_type, cpc_comments, campaign_goal) FROM stdin;
\.


--
-- Name: automation_autopilotlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('automation_autopilotlog_id_seq', 1, false);


--
-- Data for Name: automation_campaignbudgetdepletionnotification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY automation_campaignbudgetdepletionnotification (id, created_dt, available_budget, yesterdays_spend, stopped, account_manager_id, campaign_id) FROM stdin;
\.


--
-- Name: automation_campaignbudgetdepletionnotification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('automation_campaignbudgetdepletionnotification_id_seq', 1, false);


--
-- Data for Name: convapi_gareportlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY convapi_gareportlog (id, datetime, for_date, email_subject, from_address, csv_filename, ad_groups, s3_key, visits_reported, visits_imported, multimatch, multimatch_clicks, nomatch, state, errors, recipient) FROM stdin;
\.


--
-- Name: convapi_gareportlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('convapi_gareportlog_id_seq', 1, false);


--
-- Data for Name: convapi_rawgoalconversionstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY convapi_rawgoalconversionstats (id, datetime, ad_group_id, source_id, url_raw, url_clean, device_type, goal_name, z1_adgid, z1_msid, conversions, conversions_value_cc) FROM stdin;
\.


--
-- Name: convapi_rawgoalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('convapi_rawgoalconversionstats_id_seq', 1, false);


--
-- Data for Name: convapi_rawpostclickstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY convapi_rawpostclickstats (id, datetime, ad_group_id, source_id, url_raw, url_clean, device_type, z1_adgid, z1_msid, visits, new_visits, bounced_visits, pageviews, duration) FROM stdin;
\.


--
-- Name: convapi_rawpostclickstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('convapi_rawpostclickstats_id_seq', 1, false);


--
-- Data for Name: convapi_reportlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY convapi_reportlog (id, datetime, for_date, email_subject, from_address, report_filename, visits_reported, visits_imported, s3_key, state, errors, recipient) FROM stdin;
\.


--
-- Name: convapi_reportlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('convapi_reportlog_id_seq', 1, false);


--
-- Data for Name: dash_account; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_account (id, name, created_dt, modified_dt, outbrain_marketer_id, modified_by_id) FROM stdin;
\.


--
-- Data for Name: dash_account_allowed_sources; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_account_allowed_sources (id, account_id, source_id) FROM stdin;
\.


--
-- Name: dash_account_allowed_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_account_allowed_sources_id_seq', 1, false);


--
-- Data for Name: dash_account_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_account_groups (id, account_id, group_id) FROM stdin;
\.


--
-- Name: dash_account_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_account_groups_id_seq', 1, false);


--
-- Name: dash_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_account_id_seq', 1, false);


--
-- Data for Name: dash_account_users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_account_users (id, account_id, user_id) FROM stdin;
\.


--
-- Name: dash_account_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_account_users_id_seq', 1, false);


--
-- Data for Name: dash_accountsettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_accountsettings (id, name, service_fee, created_dt, archived, changes_text, account_id, created_by_id, default_account_manager_id, default_sales_representative_id) FROM stdin;
\.


--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_accountsettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroup; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroup (id, name, created_dt, modified_dt, is_demo, content_ads_tab_with_cms, campaign_id, modified_by_id) FROM stdin;
\.


--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_adgroup_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroupsettings (id, created_dt, state, start_date, end_date, cpc_cc, daily_budget_cc, target_devices, target_regions, tracking_code, enable_ga_tracking, enable_adobe_tracking, adobe_tracking_param, archived, display_url, brand_name, description, call_to_action, ad_group_name, changes_text, ad_group_id, created_by_id, ga_tracking_type, autopilot_daily_budget, autopilot_state, retargeting_ad_groups, system_user, landing_mode) FROM stdin;
\.


--
-- Name: dash_adgroupsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_adgroupsettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsource; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroupsource (id, source_campaign_key, last_successful_sync_dt, last_successful_reports_sync_dt, last_successful_status_sync_dt, can_manage_content_ads, source_content_ad_id, submission_status, submission_errors, ad_group_id, source_id, source_credentials_id) FROM stdin;
\.


--
-- Name: dash_adgroupsource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_adgroupsource_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsourcesettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroupsourcesettings (id, created_dt, state, cpc_cc, daily_budget_cc, autopilot_state, ad_group_source_id, created_by_id, landing_mode) FROM stdin;
\.


--
-- Name: dash_adgroupsourcesettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_adgroupsourcesettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsourcestate; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroupsourcestate (id, created_dt, state, cpc_cc, daily_budget_cc, ad_group_source_id) FROM stdin;
\.


--
-- Name: dash_adgroupsourcestate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_adgroupsourcestate_id_seq', 1, false);


--
-- Data for Name: dash_article; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_article (id, url, title, created_dt, ad_group_id) FROM stdin;
\.


--
-- Name: dash_article_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_article_id_seq', 1, false);


--
-- Data for Name: dash_budgethistory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_budgethistory (id, snapshot, created_dt, budget_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_budgethistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_budgethistory_id_seq', 1, false);


--
-- Data for Name: dash_budgetlineitem; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_budgetlineitem (id, start_date, end_date, amount, comment, created_dt, modified_dt, campaign_id, created_by_id, credit_id, freed_cc) FROM stdin;
\.


--
-- Name: dash_budgetlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_budgetlineitem_id_seq', 1, false);


--
-- Data for Name: dash_campaign; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaign (id, name, created_dt, modified_dt, account_id, modified_by_id) FROM stdin;
\.


--
-- Data for Name: dash_campaign_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaign_groups (id, campaign_id, group_id) FROM stdin;
\.


--
-- Name: dash_campaign_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaign_groups_id_seq', 1, false);


--
-- Name: dash_campaign_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaign_id_seq', 1, false);


--
-- Data for Name: dash_campaign_users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaign_users (id, campaign_id, user_id) FROM stdin;
\.


--
-- Name: dash_campaign_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaign_users_id_seq', 1, false);


--
-- Data for Name: dash_campaignbudgetsettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaignbudgetsettings (id, allocate, revoke, total, comment, created_dt, campaign_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_campaignbudgetsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaignbudgetsettings_id_seq', 1, false);


--
-- Data for Name: dash_campaigngoal; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaigngoal (id, type, campaign_id, created_by_id, created_dt, conversion_goal_id, "primary") FROM stdin;
\.


--
-- Name: dash_campaigngoal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaigngoal_id_seq', 1, false);


--
-- Data for Name: dash_campaigngoalvalue; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaigngoalvalue (id, value, campaign_goal_id, created_by_id, created_dt) FROM stdin;
\.


--
-- Name: dash_campaigngoalvalue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaigngoalvalue_id_seq', 1, false);


--
-- Data for Name: dash_campaignsettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_campaignsettings (id, name, created_dt, service_fee, iab_category, promotion_goal, campaign_goal, goal_quantity, target_devices, target_regions, archived, changes_text, campaign_id, created_by_id, campaign_manager_id, automatic_campaign_stop, landing_mode, system_user) FROM stdin;
\.


--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaignsettings_id_seq', 1, false);


--
-- Data for Name: dash_contentad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_contentad (id, url, title, display_url, brand_name, description, call_to_action, image_id, image_width, image_height, image_hash, crop_areas, redirect_id, created_dt, state, archived, tracker_urls, ad_group_id, batch_id) FROM stdin;
\.


--
-- Name: dash_contentad_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_contentad_id_seq', 1, false);


--
-- Data for Name: dash_contentadsource; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_contentadsource (id, submission_status, submission_errors, state, source_state, source_content_ad_id, created_dt, modified_dt, content_ad_id, source_id) FROM stdin;
\.


--
-- Name: dash_contentadsource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_contentadsource_id_seq', 1, false);


--
-- Data for Name: dash_conversiongoal; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_conversiongoal (id, type, name, conversion_window, goal_id, created_dt, campaign_id, pixel_id) FROM stdin;
\.


--
-- Name: dash_conversiongoal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_conversiongoal_id_seq', 1, false);


--
-- Data for Name: dash_conversionpixel; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_conversionpixel (id, slug, archived, last_sync_dt, created_dt, account_id) FROM stdin;
\.


--
-- Name: dash_conversionpixel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_conversionpixel_id_seq', 1, false);


--
-- Data for Name: dash_credithistory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_credithistory (id, snapshot, created_dt, created_by_id, credit_id) FROM stdin;
\.


--
-- Name: dash_credithistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_credithistory_id_seq', 1, false);


--
-- Data for Name: dash_creditlineitem; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_creditlineitem (id, start_date, end_date, amount, license_fee, status, comment, created_dt, modified_dt, account_id, created_by_id, flat_fee_cc, flat_fee_end_date, flat_fee_start_date) FROM stdin;
\.


--
-- Name: dash_creditlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_creditlineitem_id_seq', 1, false);


--
-- Data for Name: dash_defaultsourcesettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_defaultsourcesettings (id, params, default_cpc_cc, mobile_cpc_cc, daily_budget_cc, credentials_id, source_id) FROM stdin;
\.


--
-- Name: dash_defaultsourcesettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_defaultsourcesettings_id_seq', 1, false);


--
-- Data for Name: dash_demoadgrouprealadgroup; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_demoadgrouprealadgroup (id, multiplication_factor, demo_ad_group_id, real_ad_group_id) FROM stdin;
\.


--
-- Name: dash_demoadgrouprealadgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_demoadgrouprealadgroup_id_seq', 1, false);


--
-- Data for Name: dash_exportreport; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_exportreport (id, created_dt, granularity, breakdown_by_day, breakdown_by_source, order_by, additional_fields, account_id, ad_group_id, campaign_id, created_by_id, include_model_ids) FROM stdin;
\.


--
-- Data for Name: dash_exportreport_filtered_sources; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_exportreport_filtered_sources (id, exportreport_id, source_id) FROM stdin;
\.


--
-- Name: dash_exportreport_filtered_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_exportreport_filtered_sources_id_seq', 1, false);


--
-- Name: dash_exportreport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_exportreport_id_seq', 1, false);


--
-- Data for Name: dash_gaanalyticsaccount; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_gaanalyticsaccount (id, ga_account_id, ga_web_property_id, account_id) FROM stdin;
\.


--
-- Name: dash_gaanalyticsaccount_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_gaanalyticsaccount_id_seq', 1, false);


--
-- Data for Name: dash_outbrainaccount; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_outbrainaccount (id, marketer_id, used, created_dt, modified_dt, marketer_name) FROM stdin;
\.


--
-- Name: dash_outbrainaccount_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_outbrainaccount_id_seq', 1, false);


--
-- Data for Name: dash_publisherblacklist; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_publisherblacklist (id, name, everywhere, status, created_dt, account_id, ad_group_id, campaign_id, source_id, external_id) FROM stdin;
\.


--
-- Name: dash_publisherblacklist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_publisherblacklist_id_seq', 1, false);


--
-- Data for Name: dash_scheduledexportreport; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_scheduledexportreport (id, name, created_dt, state, sending_frequency, created_by_id, report_id) FROM stdin;
\.


--
-- Name: dash_scheduledexportreport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_scheduledexportreport_id_seq', 1, false);


--
-- Data for Name: dash_scheduledexportreportlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_scheduledexportreportlog (id, created_dt, start_date, end_date, report_filename, recipient_emails, state, errors, scheduled_report_id) FROM stdin;
\.


--
-- Name: dash_scheduledexportreportlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_scheduledexportreportlog_id_seq', 1, false);


--
-- Data for Name: dash_scheduledexportreportrecipient; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_scheduledexportreportrecipient (id, email, scheduled_report_id) FROM stdin;
\.


--
-- Name: dash_scheduledexportreportrecipient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_scheduledexportreportrecipient_id_seq', 1, false);


--
-- Data for Name: dash_source; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_source (id, name, tracking_slug, bidder_slug, maintenance, deprecated, created_dt, modified_dt, released, content_ad_submission_type, source_type_id, supports_retargeting, supports_retargeting_manually, default_cpc_cc, default_daily_budget_cc, default_mobile_cpc_cc) FROM stdin;
\.


--
-- Name: dash_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_source_id_seq', 1, false);


--
-- Data for Name: dash_sourcecredentials; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_sourcecredentials (id, name, credentials, created_dt, modified_dt, source_id) FROM stdin;
\.


--
-- Name: dash_sourcecredentials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_sourcecredentials_id_seq', 1, false);


--
-- Data for Name: dash_sourcetype; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_sourcetype (id, type, available_actions, min_cpc, min_daily_budget, max_cpc, max_daily_budget, cpc_decimal_places, delete_traffic_metrics_threshold, budgets_tz) FROM stdin;
\.


--
-- Name: dash_sourcetype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_sourcetype_id_seq', 1, false);


--
-- Data for Name: dash_uploadbatch; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_uploadbatch (id, name, created_dt, status, error_report_key, num_errors, processed_content_ads, inserted_content_ads, batch_size, cancelled, propagated_content_ads) FROM stdin;
\.


--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_uploadbatch_id_seq', 1, false);


--
-- Data for Name: dash_useractionlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_useractionlog (id, action_type, created_dt, account_id, account_settings_id, ad_group_id, ad_group_settings_id, campaign_id, campaign_settings_id, created_by_id) FROM stdin;
\.


--
-- Name: dash_useractionlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_useractionlog_id_seq', 1, false);


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 1, false);


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
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
11	dash	campaigngoal
12	dash	campaigngoalvalue
13	dash	sourcetype
14	dash	source
15	dash	sourcecredentials
16	dash	defaultsourcesettings
17	dash	adgroup
18	dash	adgroupsource
19	dash	adgroupsettings
20	dash	adgroupsourcestate
21	dash	adgroupsourcesettings
22	dash	uploadbatch
23	dash	contentad
24	dash	contentadsource
25	dash	article
26	dash	campaignbudgetsettings
27	dash	conversionpixel
28	dash	conversiongoal
29	dash	demoadgrouprealadgroup
30	dash	useractionlog
31	dash	publisherblacklist
32	dash	creditlineitem
33	dash	budgetlineitem
34	dash	credithistory
35	dash	budgethistory
36	dash	exportreport
37	dash	scheduledexportreport
38	dash	scheduledexportreportrecipient
39	dash	scheduledexportreportlog
40	dash	gaanalyticsaccount
41	zemauth	user
42	zemauth	internalgroup
43	actionlog	actionlogorder
44	actionlog	actionlog
45	reports	articlestats
46	reports	goalconversionstats
47	reports	adgroupstats
48	reports	adgroupgoalconversionstats
49	reports	contentadstats
50	reports	supplyreportrecipient
51	reports	contentadpostclickstats
52	reports	contentadgoalconversionstats
53	reports	budgetdailystatement
54	convapi	rawpostclickstats
55	convapi	rawgoalconversionstats
56	convapi	gareportlog
57	convapi	reportlog
58	automation	campaignbudgetdepletionnotification
59	automation	autopilotadgroupsourcebidcpclog
60	automation	autopilotlog
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('django_content_type_id_seq', 60, true);


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2016-04-07 12:50:57.392408+00
2	contenttypes	0002_remove_content_type_name	2016-04-07 12:50:57.422869+00
3	auth	0001_initial	2016-04-07 12:50:57.541966+00
4	auth	0002_alter_permission_name_max_length	2016-04-07 12:50:57.567913+00
5	auth	0003_alter_user_email_max_length	2016-04-07 12:50:57.590799+00
6	auth	0004_alter_user_username_opts	2016-04-07 12:50:57.611501+00
7	auth	0005_alter_user_last_login_null	2016-04-07 12:50:57.632479+00
8	auth	0006_require_contenttypes_0002	2016-04-07 12:50:57.640896+00
9	zemauth	0001_initial	2016-04-07 12:50:57.791885+00
10	dash	0001_initial	2016-04-07 12:51:06.631583+00
11	actionlog	0001_initial	2016-04-07 12:51:07.172156+00
12	admin	0001_initial	2016-04-07 12:51:07.361966+00
13	dash	0002_auto_20151215_1353	2016-04-07 12:51:08.143343+00
14	dash	0003_auto_20151215_1353	2016-04-07 12:51:08.1656+00
15	dash	0004_auto_20151216_0950	2016-04-07 12:51:08.334273+00
16	dash	0005_budgetlineitem_freed_cc	2016-04-07 12:51:08.473621+00
17	dash	0006_auto_20151224_1036	2016-04-07 12:51:08.579928+00
18	dash	0007_auto_20151230_1007	2016-04-07 12:51:08.682558+00
19	dash	0008_remove_campaignsettings_sales_representative	2016-04-07 12:51:08.837158+00
20	dash	0009_campaignsettings_campaign_manager	2016-04-07 12:51:08.953165+00
21	dash	0008_publisherblacklist_external_id	2016-04-07 12:51:09.064155+00
22	dash	0010_merge	2016-04-07 12:51:09.072547+00
23	dash	0011_remove_campaignsettings_account_manager	2016-04-07 12:51:09.296411+00
24	dash	0012_auto_20160115_0927	2016-04-07 12:51:09.429796+00
25	dash	0013_remove_defaultsourcesettings_auto_add	2016-04-07 12:51:09.556395+00
26	dash	0014_auto_20160121_1712	2016-04-07 12:51:09.893273+00
27	dash	0015_auto_20160121_1741	2016-04-07 12:51:10.762788+00
28	dash	0016_auto_20160126_0933	2016-04-07 12:51:11.118025+00
29	dash	0017_auto_20160127_0953	2016-04-07 12:51:11.441052+00
30	dash	0018_auto_20160127_1553	2016-04-07 12:51:11.59732+00
31	dash	0019_auto_20160201_1044	2016-04-07 12:51:12.501982+00
32	dash	0020_auto_20160201_1505	2016-04-07 12:51:12.811439+00
33	automation	0001_initial	2016-04-07 12:51:13.151775+00
34	automation	0002_autopilotlog	2016-04-07 12:51:13.332796+00
35	automation	0003_auto_20160216_1343	2016-04-07 12:51:14.024963+00
36	automation	0004_autopilotlog_campaign_goal	2016-04-07 12:51:14.173085+00
37	automation	0005_auto_20160323_1325	2016-04-07 12:51:14.317875+00
38	automation	0006_auto_20160325_1007	2016-04-07 12:51:14.458115+00
39	convapi	0001_initial	2016-04-07 12:51:14.589378+00
40	convapi	0002_auto_20151221_1558	2016-04-07 12:51:14.636922+00
41	dash	0021_auto_20160210_1545	2016-04-07 12:51:14.787624+00
42	dash	0021_adgroupsettings_retargeting_ad_groups	2016-04-07 12:51:14.984721+00
43	dash	0022_merge	2016-04-07 12:51:14.99267+00
44	dash	0023_auto_20160217_0908	2016-04-07 12:51:15.371528+00
45	dash	0023_auto_20160216_1207	2016-04-07 12:51:15.529538+00
46	dash	0024_merge	2016-04-07 12:51:15.539986+00
47	dash	0025_remove_account_uses_credits	2016-04-07 12:51:15.703346+00
48	dash	0025_auto_20160223_1016	2016-04-07 12:51:15.857635+00
49	dash	0026_merge	2016-04-07 12:51:15.86636+00
50	dash	0027_sourcetype_budgets_tz	2016-04-07 12:51:16.076286+00
51	dash	0028_campaign_landing_mode	2016-04-07 12:51:16.861722+00
52	dash	0029_auto_20160303_1708	2016-04-07 12:51:17.108546+00
53	dash	0030_source_supports_retargeting	2016-04-07 12:51:17.318259+00
54	dash	0031_auto_20160314_1442	2016-04-07 12:51:17.688408+00
55	dash	0032_auto_20160316_1633	2016-04-07 12:51:18.332277+00
56	dash	0033_auto_20160316_1335	2016-04-07 12:51:18.362017+00
57	dash	0032_auto_20160315_1204	2016-04-07 12:51:19.156987+00
58	dash	0034_merge	2016-04-07 12:51:19.166561+00
59	dash	0035_auto_20160318_1503	2016-04-07 12:51:19.203007+00
60	dash	0036_auto_20160321_1515	2016-04-07 12:51:19.979749+00
61	dash	0037_auto_20160321_1537	2016-04-07 12:51:20.586481+00
62	dash	0038_adgroupsettings_system_user	2016-04-07 12:51:20.739695+00
63	dash	0039_campaignsettings_system_user	2016-04-07 12:51:20.90383+00
64	dash	0040_auto_20160322_1637	2016-04-07 12:51:21.060712+00
65	dash	0041_auto_20160323_1325	2016-04-07 12:51:21.207707+00
66	dash	0042_auto_20160325_1007	2016-04-07 12:51:22.018374+00
67	dash	0043_auto_20160331_0937	2016-04-07 12:51:22.308007+00
68	dash	0043_adgroupsettings_landing_mode	2016-04-07 12:51:22.526256+00
69	dash	0044_merge	2016-04-07 12:51:22.534304+00
70	dash	0044_exportreport_include_model_ids	2016-04-07 12:51:22.766626+00
71	dash	0045_merge	2016-04-07 12:51:22.777828+00
72	reports	0001_initial	2016-04-07 12:51:26.64388+00
73	reports	0002_auto_20151216_0839	2016-04-07 12:51:26.886697+00
74	sessions	0001_initial	2016-04-07 12:51:26.940647+00
75	zemauth	0002_auto_20151218_1526	2016-04-07 12:51:27.108462+00
76	zemauth	0003_auto_20160107_1101	2016-04-07 12:51:27.274881+00
77	zemauth	0004_auto_20160125_1333	2016-04-07 12:51:27.439343+00
78	zemauth	0005_auto_20160128_1504	2016-04-07 12:51:27.603057+00
79	zemauth	0006_auto_20160201_1505	2016-04-07 12:51:27.767148+00
80	zemauth	0007_auto_20160202_0723	2016-04-07 12:51:27.952394+00
81	zemauth	0008_auto_20160203_1458	2016-04-07 12:51:28.126499+00
82	zemauth	0009_auto_20160205_1230	2016-04-07 12:51:28.296385+00
83	zemauth	0010_auto_20160211_0817	2016-04-07 12:51:28.491207+00
84	zemauth	0011_auto_20160211_1445	2016-04-07 12:51:28.664877+00
85	zemauth	0011_auto_20160211_1417	2016-04-07 12:51:28.846913+00
86	zemauth	0012_merge	2016-04-07 12:51:28.856741+00
87	zemauth	0013_auto_20160212_1456	2016-04-07 12:51:29.057357+00
88	zemauth	0014_auto_20160219_1754	2016-04-07 12:51:29.228713+00
89	zemauth	0015_auto_20160308_0740	2016-04-07 12:51:29.403311+00
90	zemauth	0016_auto_20160308_1703	2016-04-07 12:51:29.604811+00
91	zemauth	0017_user_is_test_user	2016-04-07 12:51:29.823717+00
92	zemauth	0016_auto_20160308_1224	2016-04-07 12:51:30.029824+00
93	zemauth	0018_merge	2016-04-07 12:51:30.041219+00
94	zemauth	0019_auto_20160312_2149	2016-04-07 12:51:30.761499+00
95	zemauth	0020_auto_20160330_0805	2016-04-07 12:51:30.905353+00
96	zemauth	0021_auto_20160331_1113	2016-04-07 12:51:31.051027+00
97	zemauth	0022_auto_20160404_0839	2016-04-07 12:59:46.738622+00
98	zemauth	0023_auto_20160404_1426	2016-04-07 12:59:46.920145+00
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('django_migrations_id_seq', 98, true);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: reports_adgroupgoalconversionstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_adgroupgoalconversionstats (id, datetime, goal_name, conversions, conversions_value_cc, ad_group_id, source_id) FROM stdin;
\.


--
-- Name: reports_adgroupgoalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_adgroupgoalconversionstats_id_seq', 1, false);


--
-- Data for Name: reports_adgroupstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_adgroupstats (id, impressions, clicks, cost_cc, data_cost_cc, visits, new_visits, bounced_visits, pageviews, duration, has_traffic_metrics, has_postclick_metrics, has_conversion_metrics, datetime, created_dt, ad_group_id, source_id) FROM stdin;
\.


--
-- Name: reports_adgroupstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_adgroupstats_id_seq', 1, false);


--
-- Data for Name: reports_articlestats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_articlestats (id, impressions, clicks, cost_cc, data_cost_cc, visits, new_visits, bounced_visits, pageviews, duration, has_traffic_metrics, has_postclick_metrics, has_conversion_metrics, datetime, created_dt, ad_group_id, article_id, source_id) FROM stdin;
\.


--
-- Name: reports_articlestats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_articlestats_id_seq', 1, false);


--
-- Data for Name: reports_budgetdailystatement; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_budgetdailystatement (id, date, media_spend_nano, data_spend_nano, license_fee_nano, budget_id) FROM stdin;
\.


--
-- Name: reports_budgetdailystatement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_budgetdailystatement_id_seq', 1, false);


--
-- Data for Name: reports_contentadgoalconversionstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_contentadgoalconversionstats (id, date, goal_type, goal_name, created_dt, conversions, content_ad_id, source_id) FROM stdin;
\.


--
-- Name: reports_contentadgoalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_contentadgoalconversionstats_id_seq', 1, false);


--
-- Data for Name: reports_contentadpostclickstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_contentadpostclickstats (id, date, created_dt, visits, new_visits, bounced_visits, pageviews, total_time_on_site, content_ad_id, source_id) FROM stdin;
\.


--
-- Name: reports_contentadpostclickstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_contentadpostclickstats_id_seq', 1, false);


--
-- Data for Name: reports_contentadstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_contentadstats (id, impressions, clicks, cost_cc, data_cost_cc, date, created_dt, content_ad_id, content_ad_source_id, source_id) FROM stdin;
\.


--
-- Name: reports_contentadstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_contentadstats_id_seq', 1, false);


--
-- Data for Name: reports_goalconversionstats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_goalconversionstats (id, datetime, goal_name, conversions, conversions_value_cc, ad_group_id, article_id, source_id) FROM stdin;
\.


--
-- Name: reports_goalconversionstats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_goalconversionstats_id_seq', 1, false);


--
-- Data for Name: reports_supplyreportrecipient; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_supplyreportrecipient (id, first_name, last_name, email, created_dt, modified_dt, source_id) FROM stdin;
\.


--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_supplyreportrecipient_id_seq', 1, false);


--
-- Data for Name: zemauth_internalgroup; Type: TABLE DATA; Schema: public; Owner: -
--

COPY zemauth_internalgroup (id, group_id) FROM stdin;
\.


--
-- Name: zemauth_internalgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('zemauth_internalgroup_id_seq', 1, false);


--
-- Data for Name: zemauth_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY zemauth_user (id, password, last_login, is_superuser, email, username, first_name, last_name, date_joined, is_staff, is_active, show_onboarding_guidance, is_test_user) FROM stdin;
\.


--
-- Data for Name: zemauth_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY zemauth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Name: zemauth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('zemauth_user_groups_id_seq', 1, false);


--
-- Name: zemauth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('zemauth_user_id_seq', 1, true);


--
-- Data for Name: zemauth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY zemauth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Name: zemauth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('zemauth_user_user_permissions_id_seq', 1, false);


--
-- Name: actionlog_actionlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_actionlog_pkey PRIMARY KEY (id);


--
-- Name: actionlog_actionlogorder_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY actionlog_actionlogorder
    ADD CONSTRAINT actionlog_actionlogorder_pkey PRIMARY KEY (id);


--
-- Name: auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions_group_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission_content_type_id_codename_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_key UNIQUE (content_type_id, codename);


--
-- Name: auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_autopilotadgroupsourcebidcpclog_pkey PRIMARY KEY (id);


--
-- Name: automation_autopilotlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY automation_autopilotlog
    ADD CONSTRAINT automation_autopilotlog_pkey PRIMARY KEY (id);


--
-- Name: automation_campaignbudgetdepletionnotification_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_campaignbudgetdepletionnotification_pkey PRIMARY KEY (id);


--
-- Name: convapi_gareportlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY convapi_gareportlog
    ADD CONSTRAINT convapi_gareportlog_pkey PRIMARY KEY (id);


--
-- Name: convapi_rawgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY convapi_rawgoalconversionstats
    ADD CONSTRAINT convapi_rawgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: convapi_rawpostclickstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY convapi_rawpostclickstats
    ADD CONSTRAINT convapi_rawpostclickstats_pkey PRIMARY KEY (id);


--
-- Name: convapi_reportlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY convapi_reportlog
    ADD CONSTRAINT convapi_reportlog_pkey PRIMARY KEY (id);


--
-- Name: dash_account_allowed_sources_account_id_source_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allowed_sources_account_id_source_id_key UNIQUE (account_id, source_id);


--
-- Name: dash_account_allowed_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allowed_sources_pkey PRIMARY KEY (id);


--
-- Name: dash_account_groups_account_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_account_id_group_id_key UNIQUE (account_id, group_id);


--
-- Name: dash_account_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_pkey PRIMARY KEY (id);


--
-- Name: dash_account_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_name_key UNIQUE (name);


--
-- Name: dash_account_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_pkey PRIMARY KEY (id);


--
-- Name: dash_account_users_account_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_account_id_user_id_key UNIQUE (account_id, user_id);


--
-- Name: dash_account_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_pkey PRIMARY KEY (id);


--
-- Name: dash_accountsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsource_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsourcesettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgroupsourcesettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsourcestate_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_adgroupsourcestate
    ADD CONSTRAINT dash_adgroupsourcestate_pkey PRIMARY KEY (id);


--
-- Name: dash_article_ad_group_id_3e67a346ec46475b_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_ad_group_id_3e67a346ec46475b_uniq UNIQUE (ad_group_id, url, title);


--
-- Name: dash_article_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_pkey PRIMARY KEY (id);


--
-- Name: dash_budgethistory_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethistory_pkey PRIMARY KEY (id);


--
-- Name: dash_budgetlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlineitem_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_groups_campaign_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_campaign_id_group_id_key UNIQUE (campaign_id, group_id);


--
-- Name: dash_campaign_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_users_campaign_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_campaign_id_user_id_key UNIQUE (campaign_id, user_id);


--
-- Name: dash_campaign_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_pkey PRIMARY KEY (id);


--
-- Name: dash_campaignbudgetsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaignbudgetsettings
    ADD CONSTRAINT dash_campaignbudgetsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_campaigngoal_campaign_id_2e8871dad2b38e5d_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigngoal_campaign_id_2e8871dad2b38e5d_uniq UNIQUE (campaign_id, type, conversion_goal_id);


--
-- Name: dash_campaigngoal_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigngoal_pkey PRIMARY KEY (id);


--
-- Name: dash_campaigngoalvalue_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaigngoalvalue
    ADD CONSTRAINT dash_campaigngoalvalue_pkey PRIMARY KEY (id);


--
-- Name: dash_campaignsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaignsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_contentad_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_pkey PRIMARY KEY (id);


--
-- Name: dash_contentadsource_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsource_pkey PRIMARY KEY (id);


--
-- Name: dash_conversiongoal_campaign_id_2f842d4d685c8de7_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_2f842d4d685c8de7_uniq UNIQUE (campaign_id, type, goal_id);


--
-- Name: dash_conversiongoal_campaign_id_62decd992187eef7_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_62decd992187eef7_uniq UNIQUE (campaign_id, name);


--
-- Name: dash_conversiongoal_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_pkey PRIMARY KEY (id);


--
-- Name: dash_conversionpixel_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_pkey PRIMARY KEY (id);


--
-- Name: dash_conversionpixel_slug_65b87bfffd455d67_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_slug_65b87bfffd455d67_uniq UNIQUE (slug, account_id);


--
-- Name: dash_credithistory_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithistory_pkey PRIMARY KEY (id);


--
-- Name: dash_creditlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlineitem_pkey PRIMARY KEY (id);


--
-- Name: dash_defaultsourcesettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_pkey PRIMARY KEY (id);


--
-- Name: dash_defaultsourcesettings_source_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_source_id_key UNIQUE (source_id);


--
-- Name: dash_demoadgrouprealadgroup_demo_ad_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoadgrouprealadgroup_demo_ad_group_id_key UNIQUE (demo_ad_group_id);


--
-- Name: dash_demoadgrouprealadgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoadgrouprealadgroup_pkey PRIMARY KEY (id);


--
-- Name: dash_demoadgrouprealadgroup_real_ad_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoadgrouprealadgroup_real_ad_group_id_key UNIQUE (real_ad_group_id);


--
-- Name: dash_exportreport_filtered_source_exportreport_id_source_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_source_exportreport_id_source_id_key UNIQUE (exportreport_id, source_id);


--
-- Name: dash_exportreport_filtered_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_sources_pkey PRIMARY KEY (id);


--
-- Name: dash_exportreport_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_pkey PRIMARY KEY (id);


--
-- Name: dash_gaanalyticsaccount_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_gaanalyticsaccount
    ADD CONSTRAINT dash_gaanalyticsaccount_pkey PRIMARY KEY (id);


--
-- Name: dash_outbrainaccount_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_outbrainaccount
    ADD CONSTRAINT dash_outbrainaccount_pkey PRIMARY KEY (id);


--
-- Name: dash_publisherblacklist_name_2eec92a070a4cbb8_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_name_2eec92a070a4cbb8_uniq UNIQUE (name, everywhere, account_id, campaign_id, ad_group_id, source_id);


--
-- Name: dash_publisherblacklist_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportr_scheduled_report_id_4d149aaafb5876bc_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT dash_scheduledexportr_scheduled_report_id_4d149aaafb5876bc_uniq UNIQUE (scheduled_report_id, email);


--
-- Name: dash_scheduledexportreport_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_scheduledexportreport_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportreportlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_scheduledexportreportlog
    ADD CONSTRAINT dash_scheduledexportreportlog_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportreportrecipient_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT dash_scheduledexportreportrecipient_pkey PRIMARY KEY (id);


--
-- Name: dash_source_bidder_slug_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_bidder_slug_key UNIQUE (bidder_slug);


--
-- Name: dash_source_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_pkey PRIMARY KEY (id);


--
-- Name: dash_source_tracking_slug_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_tracking_slug_key UNIQUE (tracking_slug);


--
-- Name: dash_sourcecredentials_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_sourcecredentials
    ADD CONSTRAINT dash_sourcecredentials_pkey PRIMARY KEY (id);


--
-- Name: dash_sourcetype_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_sourcetype
    ADD CONSTRAINT dash_sourcetype_pkey PRIMARY KEY (id);


--
-- Name: dash_sourcetype_type_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_sourcetype
    ADD CONSTRAINT dash_sourcetype_type_key UNIQUE (type);


--
-- Name: dash_uploadbatch_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_uploadbatch
    ADD CONSTRAINT dash_uploadbatch_pkey PRIMARY KEY (id);


--
-- Name: dash_useractionlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractionlog_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type_app_label_45f3b1d93ec8c61c_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_45f3b1d93ec8c61c_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: reports_adgroupgoalconversionsta_datetime_64c6effdb1878da9_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconversionsta_datetime_64c6effdb1878da9_uniq UNIQUE (datetime, ad_group_id, source_id, goal_name);


--
-- Name: reports_adgroupgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_adgroupstats_datetime_61985984b28519c1_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_datetime_61985984b28519c1_uniq UNIQUE (datetime, ad_group_id, source_id);


--
-- Name: reports_adgroupstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_pkey PRIMARY KEY (id);


--
-- Name: reports_articlestats_datetime_22035dbdd8455a0c_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_datetime_22035dbdd8455a0c_uniq UNIQUE (datetime, ad_group_id, article_id, source_id);


--
-- Name: reports_articlestats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_pkey PRIMARY KEY (id);


--
-- Name: reports_budgetdailystatement_budget_id_5d79cade1e21439d_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_budgetdailystatement
    ADD CONSTRAINT reports_budgetdailystatement_budget_id_5d79cade1e21439d_uniq UNIQUE (budget_id, date);


--
-- Name: reports_budgetdailystatement_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_budgetdailystatement
    ADD CONSTRAINT reports_budgetdailystatement_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadgoalconversionstats_date_2075955a8d03dddc_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconversionstats_date_2075955a8d03dddc_uniq UNIQUE (date, content_ad_id, source_id, goal_type, goal_name);


--
-- Name: reports_contentadgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadpostclickstats_date_2400403d2fcae43d_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclickstats_date_2400403d2fcae43d_uniq UNIQUE (date, content_ad_id, source_id);


--
-- Name: reports_contentadpostclickstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclickstats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadstats_date_4bd0def2cd7fded4_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_date_4bd0def2cd7fded4_uniq UNIQUE (date, content_ad_source_id);


--
-- Name: reports_contentadstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_pkey PRIMARY KEY (id);


--
-- Name: reports_goalconversionstats_datetime_1095ea069adf2ffd_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstats_datetime_1095ea069adf2ffd_uniq UNIQUE (datetime, ad_group_id, article_id, source_id, goal_name);


--
-- Name: reports_goalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_supplyreportrecipient_email_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyreportrecipient_email_key UNIQUE (email);


--
-- Name: reports_supplyreportrecipient_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyreportrecipient_pkey PRIMARY KEY (id);


--
-- Name: zemauth_internalgroup_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_group_id_key UNIQUE (group_id);


--
-- Name: zemauth_internalgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_email_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_user
    ADD CONSTRAINT zemauth_user_email_key UNIQUE (email);


--
-- Name: zemauth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: zemauth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_user
    ADD CONSTRAINT zemauth_user_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: actionlog_actionlog_0b893638; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_0b893638 ON actionlog_actionlog USING btree (created_dt);


--
-- Name: actionlog_actionlog_418c5509; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_418c5509 ON actionlog_actionlog USING btree (action);


--
-- Name: actionlog_actionlog_69dfcb07; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_69dfcb07 ON actionlog_actionlog USING btree (order_id);


--
-- Name: actionlog_actionlog_87f78d4d; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_87f78d4d ON actionlog_actionlog USING btree (content_ad_source_id);


--
-- Name: actionlog_actionlog_9ed39e2e; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_9ed39e2e ON actionlog_actionlog USING btree (state);


--
-- Name: actionlog_actionlog_a8060d34; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_a8060d34 ON actionlog_actionlog USING btree (ad_group_source_id);


--
-- Name: actionlog_actionlog_action_1d19c831f66c7e23_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_action_1d19c831f66c7e23_like ON actionlog_actionlog USING btree (action varchar_pattern_ops);


--
-- Name: actionlog_actionlog_b3da0983; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_b3da0983 ON actionlog_actionlog USING btree (modified_by_id);


--
-- Name: actionlog_actionlog_c3fc31da; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_c3fc31da ON actionlog_actionlog USING btree (modified_dt);


--
-- Name: actionlog_actionlog_ca47336a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_ca47336a ON actionlog_actionlog USING btree (action_type);


--
-- Name: actionlog_actionlog_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_e93cb7eb ON actionlog_actionlog USING btree (created_by_id);


--
-- Name: actionlog_actionlog_id_15546055dcb172b4_idx; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX actionlog_actionlog_id_15546055dcb172b4_idx ON actionlog_actionlog USING btree (id, created_dt);


--
-- Name: auth_group_name_253ae2a6331666e8_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX auth_group_name_253ae2a6331666e8_like ON auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_0e939a4f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX auth_group_permissions_0e939a4f ON auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_8373b171; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX auth_group_permissions_8373b171 ON auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_417f1b1c; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX auth_permission_417f1b1c ON auth_permission USING btree (content_type_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_0b893638; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_0b893638 ON automation_autopilotadgroupsourcebidcpclog USING btree (created_dt);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_22ff94c4 ON automation_autopilotadgroupsourcebidcpclog USING btree (ad_group_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_a8060d34; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_a8060d34 ON automation_autopilotadgroupsourcebidcpclog USING btree (ad_group_source_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_f14acec3 ON automation_autopilotadgroupsourcebidcpclog USING btree (campaign_id);


--
-- Name: automation_autopilotlog_0b893638; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotlog_0b893638 ON automation_autopilotlog USING btree (created_dt);


--
-- Name: automation_autopilotlog_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotlog_22ff94c4 ON automation_autopilotlog USING btree (ad_group_id);


--
-- Name: automation_autopilotlog_a8060d34; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_autopilotlog_a8060d34 ON automation_autopilotlog USING btree (ad_group_source_id);


--
-- Name: automation_campaignbudgetdepletionnotification_0b893638; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_campaignbudgetdepletionnotification_0b893638 ON automation_campaignbudgetdepletionnotification USING btree (created_dt);


--
-- Name: automation_campaignbudgetdepletionnotification_6bc80cbd; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_campaignbudgetdepletionnotification_6bc80cbd ON automation_campaignbudgetdepletionnotification USING btree (account_manager_id);


--
-- Name: automation_campaignbudgetdepletionnotification_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX automation_campaignbudgetdepletionnotification_f14acec3 ON automation_campaignbudgetdepletionnotification USING btree (campaign_id);


--
-- Name: dash_account_allowed_sources_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_allowed_sources_0afd9202 ON dash_account_allowed_sources USING btree (source_id);


--
-- Name: dash_account_allowed_sources_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_allowed_sources_8a089c2a ON dash_account_allowed_sources USING btree (account_id);


--
-- Name: dash_account_b3da0983; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_b3da0983 ON dash_account USING btree (modified_by_id);


--
-- Name: dash_account_groups_0e939a4f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_groups_0e939a4f ON dash_account_groups USING btree (group_id);


--
-- Name: dash_account_groups_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_groups_8a089c2a ON dash_account_groups USING btree (account_id);


--
-- Name: dash_account_name_19b118db2a741bd8_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_name_19b118db2a741bd8_like ON dash_account USING btree (name varchar_pattern_ops);


--
-- Name: dash_account_users_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_users_8a089c2a ON dash_account_users USING btree (account_id);


--
-- Name: dash_account_users_e8701ad4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_account_users_e8701ad4 ON dash_account_users USING btree (user_id);


--
-- Name: dash_accountsettings_49e3f602; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_accountsettings_49e3f602 ON dash_accountsettings USING btree (default_account_manager_id);


--
-- Name: dash_accountsettings_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_accountsettings_8a089c2a ON dash_accountsettings USING btree (account_id);


--
-- Name: dash_accountsettings_b6c58ed1; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_accountsettings_b6c58ed1 ON dash_accountsettings USING btree (default_sales_representative_id);


--
-- Name: dash_accountsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_accountsettings_e93cb7eb ON dash_accountsettings USING btree (created_by_id);


--
-- Name: dash_adgroup_b3da0983; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroup_b3da0983 ON dash_adgroup USING btree (modified_by_id);


--
-- Name: dash_adgroup_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroup_f14acec3 ON dash_adgroup USING btree (campaign_id);


--
-- Name: dash_adgroupsettings_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsettings_22ff94c4 ON dash_adgroupsettings USING btree (ad_group_id);


--
-- Name: dash_adgroupsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsettings_e93cb7eb ON dash_adgroupsettings USING btree (created_by_id);


--
-- Name: dash_adgroupsource_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsource_0afd9202 ON dash_adgroupsource USING btree (source_id);


--
-- Name: dash_adgroupsource_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsource_22ff94c4 ON dash_adgroupsource USING btree (ad_group_id);


--
-- Name: dash_adgroupsource_709deb08; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsource_709deb08 ON dash_adgroupsource USING btree (source_credentials_id);


--
-- Name: dash_adgroupsourcesettings_a8060d34; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsourcesettings_a8060d34 ON dash_adgroupsourcesettings USING btree (ad_group_source_id);


--
-- Name: dash_adgroupsourcesettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsourcesettings_e93cb7eb ON dash_adgroupsourcesettings USING btree (created_by_id);


--
-- Name: dash_adgroupsourcestate_a8060d34; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_adgroupsourcestate_a8060d34 ON dash_adgroupsourcestate USING btree (ad_group_source_id);


--
-- Name: dash_article_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_article_22ff94c4 ON dash_article USING btree (ad_group_id);


--
-- Name: dash_budgethistory_7748a592; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_budgethistory_7748a592 ON dash_budgethistory USING btree (budget_id);


--
-- Name: dash_budgethistory_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_budgethistory_e93cb7eb ON dash_budgethistory USING btree (created_by_id);


--
-- Name: dash_budgetlineitem_5097e6b2; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_budgetlineitem_5097e6b2 ON dash_budgetlineitem USING btree (credit_id);


--
-- Name: dash_budgetlineitem_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_budgetlineitem_e93cb7eb ON dash_budgetlineitem USING btree (created_by_id);


--
-- Name: dash_budgetlineitem_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_budgetlineitem_f14acec3 ON dash_budgetlineitem USING btree (campaign_id);


--
-- Name: dash_campaign_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaign_8a089c2a ON dash_campaign USING btree (account_id);


--
-- Name: dash_campaign_b3da0983; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaign_b3da0983 ON dash_campaign USING btree (modified_by_id);


--
-- Name: dash_campaign_groups_0e939a4f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaign_groups_0e939a4f ON dash_campaign_groups USING btree (group_id);


--
-- Name: dash_campaign_groups_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaign_groups_f14acec3 ON dash_campaign_groups USING btree (campaign_id);


--
-- Name: dash_campaign_users_e8701ad4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaign_users_e8701ad4 ON dash_campaign_users USING btree (user_id);


--
-- Name: dash_campaign_users_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaign_users_f14acec3 ON dash_campaign_users USING btree (campaign_id);


--
-- Name: dash_campaignbudgetsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignbudgetsettings_e93cb7eb ON dash_campaignbudgetsettings USING btree (created_by_id);


--
-- Name: dash_campaignbudgetsettings_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignbudgetsettings_f14acec3 ON dash_campaignbudgetsettings USING btree (campaign_id);


--
-- Name: dash_campaigngoal_b216c85c; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaigngoal_b216c85c ON dash_campaigngoal USING btree (conversion_goal_id);


--
-- Name: dash_campaigngoal_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaigngoal_e93cb7eb ON dash_campaigngoal USING btree (created_by_id);


--
-- Name: dash_campaigngoal_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaigngoal_f14acec3 ON dash_campaigngoal USING btree (campaign_id);


--
-- Name: dash_campaigngoalvalue_80fa406a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaigngoalvalue_80fa406a ON dash_campaigngoalvalue USING btree (campaign_goal_id);


--
-- Name: dash_campaigngoalvalue_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaigngoalvalue_e93cb7eb ON dash_campaigngoalvalue USING btree (created_by_id);


--
-- Name: dash_campaignsettings_548b53b3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignsettings_548b53b3 ON dash_campaignsettings USING btree (iab_category);


--
-- Name: dash_campaignsettings_dd7656fc; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignsettings_dd7656fc ON dash_campaignsettings USING btree (campaign_manager_id);


--
-- Name: dash_campaignsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignsettings_e93cb7eb ON dash_campaignsettings USING btree (created_by_id);


--
-- Name: dash_campaignsettings_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignsettings_f14acec3 ON dash_campaignsettings USING btree (campaign_id);


--
-- Name: dash_campaignsettings_iab_category_15c36af04da422c5_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_campaignsettings_iab_category_15c36af04da422c5_like ON dash_campaignsettings USING btree (iab_category varchar_pattern_ops);


--
-- Name: dash_contentad_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_contentad_22ff94c4 ON dash_contentad USING btree (ad_group_id);


--
-- Name: dash_contentad_d4e60137; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_contentad_d4e60137 ON dash_contentad USING btree (batch_id);


--
-- Name: dash_contentadsource_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_contentadsource_0afd9202 ON dash_contentadsource USING btree (source_id);


--
-- Name: dash_contentadsource_abf89b3f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_contentadsource_abf89b3f ON dash_contentadsource USING btree (content_ad_id);


--
-- Name: dash_conversiongoal_ba2eed6c; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_conversiongoal_ba2eed6c ON dash_conversiongoal USING btree (pixel_id);


--
-- Name: dash_conversiongoal_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_conversiongoal_f14acec3 ON dash_conversiongoal USING btree (campaign_id);


--
-- Name: dash_conversionpixel_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_conversionpixel_8a089c2a ON dash_conversionpixel USING btree (account_id);


--
-- Name: dash_credithistory_5097e6b2; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_credithistory_5097e6b2 ON dash_credithistory USING btree (credit_id);


--
-- Name: dash_credithistory_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_credithistory_e93cb7eb ON dash_credithistory USING btree (created_by_id);


--
-- Name: dash_creditlineitem_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_creditlineitem_8a089c2a ON dash_creditlineitem USING btree (account_id);


--
-- Name: dash_creditlineitem_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_creditlineitem_e93cb7eb ON dash_creditlineitem USING btree (created_by_id);


--
-- Name: dash_defaultsourcesettings_9d2c2cd1; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_defaultsourcesettings_9d2c2cd1 ON dash_defaultsourcesettings USING btree (credentials_id);


--
-- Name: dash_exportreport_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_exportreport_22ff94c4 ON dash_exportreport USING btree (ad_group_id);


--
-- Name: dash_exportreport_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_exportreport_8a089c2a ON dash_exportreport USING btree (account_id);


--
-- Name: dash_exportreport_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_exportreport_e93cb7eb ON dash_exportreport USING btree (created_by_id);


--
-- Name: dash_exportreport_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_exportreport_f14acec3 ON dash_exportreport USING btree (campaign_id);


--
-- Name: dash_exportreport_filtered_sources_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_exportreport_filtered_sources_0afd9202 ON dash_exportreport_filtered_sources USING btree (source_id);


--
-- Name: dash_exportreport_filtered_sources_aa7beb1a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_exportreport_filtered_sources_aa7beb1a ON dash_exportreport_filtered_sources USING btree (exportreport_id);


--
-- Name: dash_gaanalyticsaccount_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_gaanalyticsaccount_8a089c2a ON dash_gaanalyticsaccount USING btree (account_id);


--
-- Name: dash_publisherblacklist_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_publisherblacklist_0afd9202 ON dash_publisherblacklist USING btree (source_id);


--
-- Name: dash_publisherblacklist_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_publisherblacklist_22ff94c4 ON dash_publisherblacklist USING btree (ad_group_id);


--
-- Name: dash_publisherblacklist_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_publisherblacklist_8a089c2a ON dash_publisherblacklist USING btree (account_id);


--
-- Name: dash_publisherblacklist_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_publisherblacklist_f14acec3 ON dash_publisherblacklist USING btree (campaign_id);


--
-- Name: dash_scheduledexportreport_6f78b20c; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_scheduledexportreport_6f78b20c ON dash_scheduledexportreport USING btree (report_id);


--
-- Name: dash_scheduledexportreport_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_scheduledexportreport_e93cb7eb ON dash_scheduledexportreport USING btree (created_by_id);


--
-- Name: dash_scheduledexportreportlog_4deefed9; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_scheduledexportreportlog_4deefed9 ON dash_scheduledexportreportlog USING btree (scheduled_report_id);


--
-- Name: dash_scheduledexportreportrecipient_4deefed9; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_scheduledexportreportrecipient_4deefed9 ON dash_scheduledexportreportrecipient USING btree (scheduled_report_id);


--
-- Name: dash_source_bidder_slug_586d3ce9c27074e5_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_source_bidder_slug_586d3ce9c27074e5_like ON dash_source USING btree (bidder_slug varchar_pattern_ops);


--
-- Name: dash_source_ed5cb66b; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_source_ed5cb66b ON dash_source USING btree (source_type_id);


--
-- Name: dash_source_tracking_slug_5a752ff2b6c2b16_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_source_tracking_slug_5a752ff2b6c2b16_like ON dash_source USING btree (tracking_slug varchar_pattern_ops);


--
-- Name: dash_sourcecredentials_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_sourcecredentials_0afd9202 ON dash_sourcecredentials USING btree (source_id);


--
-- Name: dash_sourcetype_type_7b056ce1a0b025c4_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_sourcetype_type_7b056ce1a0b025c4_like ON dash_sourcetype USING btree (type varchar_pattern_ops);


--
-- Name: dash_useractionlog_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_22ff94c4 ON dash_useractionlog USING btree (ad_group_id);


--
-- Name: dash_useractionlog_83d504ef; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_83d504ef ON dash_useractionlog USING btree (campaign_settings_id);


--
-- Name: dash_useractionlog_8a089c2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_8a089c2a ON dash_useractionlog USING btree (account_id);


--
-- Name: dash_useractionlog_c9776e2a; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_c9776e2a ON dash_useractionlog USING btree (account_settings_id);


--
-- Name: dash_useractionlog_e93cb7eb; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_e93cb7eb ON dash_useractionlog USING btree (created_by_id);


--
-- Name: dash_useractionlog_f14acec3; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_f14acec3 ON dash_useractionlog USING btree (campaign_id);


--
-- Name: dash_useractionlog_f83e08e7; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX dash_useractionlog_f83e08e7 ON dash_useractionlog USING btree (ad_group_settings_id);


--
-- Name: django_admin_log_417f1b1c; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX django_admin_log_417f1b1c ON django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_e8701ad4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX django_admin_log_e8701ad4 ON django_admin_log USING btree (user_id);


--
-- Name: django_session_de54fa62; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX django_session_de54fa62 ON django_session USING btree (expire_date);


--
-- Name: django_session_session_key_461cfeaa630ca218_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX django_session_session_key_461cfeaa630ca218_like ON django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: reports_adgroupgoalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_adgroupgoalconversionstats_0afd9202 ON reports_adgroupgoalconversionstats USING btree (source_id);


--
-- Name: reports_adgroupgoalconversionstats_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_adgroupgoalconversionstats_22ff94c4 ON reports_adgroupgoalconversionstats USING btree (ad_group_id);


--
-- Name: reports_adgroupstats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_adgroupstats_0afd9202 ON reports_adgroupstats USING btree (source_id);


--
-- Name: reports_adgroupstats_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_adgroupstats_22ff94c4 ON reports_adgroupstats USING btree (ad_group_id);


--
-- Name: reports_articlestats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_articlestats_0afd9202 ON reports_articlestats USING btree (source_id);


--
-- Name: reports_articlestats_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_articlestats_22ff94c4 ON reports_articlestats USING btree (ad_group_id);


--
-- Name: reports_articlestats_a00c1b00; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_articlestats_a00c1b00 ON reports_articlestats USING btree (article_id);


--
-- Name: reports_articlestats_ad_group_id_23b66c4e28e5d810_idx; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_articlestats_ad_group_id_23b66c4e28e5d810_idx ON reports_articlestats USING btree (ad_group_id, datetime);


--
-- Name: reports_budgetdailystatement_7748a592; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_budgetdailystatement_7748a592 ON reports_budgetdailystatement USING btree (budget_id);


--
-- Name: reports_contentadgoalconversion_goal_type_55f1cce1d23e0872_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadgoalconversion_goal_type_55f1cce1d23e0872_like ON reports_contentadgoalconversionstats USING btree (goal_type varchar_pattern_ops);


--
-- Name: reports_contentadgoalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadgoalconversionstats_0afd9202 ON reports_contentadgoalconversionstats USING btree (source_id);


--
-- Name: reports_contentadgoalconversionstats_197e2321; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadgoalconversionstats_197e2321 ON reports_contentadgoalconversionstats USING btree (goal_type);


--
-- Name: reports_contentadgoalconversionstats_abf89b3f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadgoalconversionstats_abf89b3f ON reports_contentadgoalconversionstats USING btree (content_ad_id);


--
-- Name: reports_contentadpostclickstats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadpostclickstats_0afd9202 ON reports_contentadpostclickstats USING btree (source_id);


--
-- Name: reports_contentadpostclickstats_abf89b3f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadpostclickstats_abf89b3f ON reports_contentadpostclickstats USING btree (content_ad_id);


--
-- Name: reports_contentadstats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadstats_0afd9202 ON reports_contentadstats USING btree (source_id);


--
-- Name: reports_contentadstats_87f78d4d; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadstats_87f78d4d ON reports_contentadstats USING btree (content_ad_source_id);


--
-- Name: reports_contentadstats_abf89b3f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_contentadstats_abf89b3f ON reports_contentadstats USING btree (content_ad_id);


--
-- Name: reports_goalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_goalconversionstats_0afd9202 ON reports_goalconversionstats USING btree (source_id);


--
-- Name: reports_goalconversionstats_22ff94c4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_goalconversionstats_22ff94c4 ON reports_goalconversionstats USING btree (ad_group_id);


--
-- Name: reports_goalconversionstats_a00c1b00; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_goalconversionstats_a00c1b00 ON reports_goalconversionstats USING btree (article_id);


--
-- Name: reports_supplyreportrecipient_0afd9202; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_supplyreportrecipient_0afd9202 ON reports_supplyreportrecipient USING btree (source_id);


--
-- Name: reports_supplyreportrecipient_email_4176c5f708509f21_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX reports_supplyreportrecipient_email_4176c5f708509f21_like ON reports_supplyreportrecipient USING btree (email varchar_pattern_ops);


--
-- Name: zemauth_user_email_660817d9030478bc_like; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX zemauth_user_email_660817d9030478bc_like ON zemauth_user USING btree (email varchar_pattern_ops);


--
-- Name: zemauth_user_email_idx; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user USING btree (lower((email)::text));


--
-- Name: zemauth_user_groups_0e939a4f; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX zemauth_user_groups_0e939a4f ON zemauth_user_groups USING btree (group_id);


--
-- Name: zemauth_user_groups_e8701ad4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX zemauth_user_groups_e8701ad4 ON zemauth_user_groups USING btree (user_id);


--
-- Name: zemauth_user_user_permissions_8373b171; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX zemauth_user_user_permissions_8373b171 ON zemauth_user_user_permissions USING btree (permission_id);


--
-- Name: zemauth_user_user_permissions_e8701ad4; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX zemauth_user_user_permissions_e8701ad4 ON zemauth_user_user_permissions USING btree (user_id);


--
-- Name: D0f4d235d0f00cd5dd46cef53fe328dd; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportlog
    ADD CONSTRAINT "D0f4d235d0f00cd5dd46cef53fe328dd" FOREIGN KEY (scheduled_report_id) REFERENCES dash_scheduledexportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D125e6979c26170e2897cb6b9fbf4a40; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT "D125e6979c26170e2897cb6b9fbf4a40" FOREIGN KEY (content_ad_source_id) REFERENCES dash_contentadsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D1f056134358335d812a106bbecb1388; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT "D1f056134358335d812a106bbecb1388" FOREIGN KEY (campaign_settings_id) REFERENCES dash_campaignsettings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D222020c4260fb940f1128384ef4e2a7; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT "D222020c4260fb940f1128384ef4e2a7" FOREIGN KEY (ad_group_settings_id) REFERENCES dash_adgroupsettings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D274f17960266a723e91a879b2938262; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT "D274f17960266a723e91a879b2938262" FOREIGN KEY (account_settings_id) REFERENCES dash_accountsettings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D413a31aad54ed2eab2cb3d0ca1ab26c; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT "D413a31aad54ed2eab2cb3d0ca1ab26c" FOREIGN KEY (content_ad_source_id) REFERENCES dash_contentadsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D4544a30d85cbe2065bcc9b246c9c634; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT "D4544a30d85cbe2065bcc9b246c9c634" FOREIGN KEY (scheduled_report_id) REFERENCES dash_scheduledexportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: D91cbf98fff489f9af35a0c541a63e72; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT "D91cbf98fff489f9af35a0c541a63e72" FOREIGN KEY (default_sales_representative_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ac_ad_group_source_id_5e35b3055fbd3996_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT ac_ad_group_source_id_5e35b3055fbd3996_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: action_order_id_5ef59bd83a8712b3_fk_actionlog_actionlogorder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT action_order_id_5ef59bd83a8712b3_fk_actionlog_actionlogorder_id FOREIGN KEY (order_id) REFERENCES actionlog_actionlogorder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_ac_modified_by_id_7e7800cd3127e10c_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_ac_modified_by_id_7e7800cd3127e10c_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_act_created_by_id_3390c632a986e386_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_act_created_by_id_3390c632a986e386_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ad66818816910836382ffefc141f280b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT ad66818816910836382ffefc141f280b FOREIGN KEY (source_credentials_id) REFERENCES dash_sourcecredentials(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: au_ad_group_source_id_5fe2bc0149fd4887_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT au_ad_group_source_id_5fe2bc0149fd4887_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: au_ad_group_source_id_70c32f2b28612792_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog
    ADD CONSTRAINT au_ad_group_source_id_70c32f2b28612792_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_content_type_id_508cf46651277a81_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_content_type_id_508cf46651277a81_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissio_group_id_689710a9a73b7457_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_group_id_689710a9a73b7457_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permission_id_1f49ccbbdc69d2fc_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permission_id_1f49ccbbdc69d2fc_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automati_account_manager_id_5101fb4db2987ac8_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automati_account_manager_id_5101fb4db2987ac8_fk_zemauth_user_id FOREIGN KEY (account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_aut_campaign_id_7870d80a2067c501_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_aut_campaign_id_7870d80a2067c501_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_auto_ad_group_id_29353cf823fae1c4_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_auto_ad_group_id_29353cf823fae1c4_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_auto_ad_group_id_70433b3e904d4c89_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog
    ADD CONSTRAINT automation_auto_ad_group_id_70433b3e904d4c89_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_cam_campaign_id_6385ff5672ab2818_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_cam_campaign_id_6385ff5672ab2818_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: d_conversion_goal_id_7c310810323e6316_fk_dash_conversiongoal_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT d_conversion_goal_id_7c310810323e6316_fk_dash_conversiongoal_id FOREIGN KEY (conversion_goal_id) REFERENCES dash_conversiongoal(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: da_ad_group_source_id_75e25e0c8b4d572d_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT da_ad_group_source_id_75e25e0c8b4d572d_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: da_credentials_id_69620f152a4e171d_fk_dash_sourcecredentials_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT da_credentials_id_69620f152a4e171d_fk_dash_sourcecredentials_id FOREIGN KEY (credentials_id) REFERENCES dash_sourcecredentials(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: das_ad_group_source_id_2bc2e2112081f6e_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcestate
    ADD CONSTRAINT das_ad_group_source_id_2bc2e2112081f6e_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash__campaign_goal_id_7b30d80a20518db6_fk_dash_campaigngoal_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue
    ADD CONSTRAINT dash__campaign_goal_id_7b30d80a20518db6_fk_dash_campaigngoal_id FOREIGN KEY (campaign_goal_id) REFERENCES dash_campaigngoal(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_all_account_id_2073e91cfafb504a_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_all_account_id_2073e91cfafb504a_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_allow_source_id_7f02f399cc379663_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allow_source_id_7f02f399cc379663_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_gro_account_id_205f51ea0c4ba450_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_gro_account_id_205f51ea0c4ba450_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_groups_group_id_4631fc181ad52fa_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_group_id_4631fc181ad52fa_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_modified_by_id_3d51056119a59652_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_modified_by_id_3d51056119a59652_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_use_account_id_5e11b94fe9e97351_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_use_account_id_5e11b94fe9e97351_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_users_user_id_511c184c0aeb2754_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_user_id_511c184c0aeb2754_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountse_created_by_id_612e6ccad05f5e3_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountse_created_by_id_612e6ccad05f5e3_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountsett_account_id_3a5781fd9c53d8a1_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsett_account_id_3a5781fd9c53d8a1_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroup_campaign_id_7c0846f18af72a69_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_campaign_id_7c0846f18af72a69_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroup_modified_by_id_6957fb50d67cccf9_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_modified_by_id_6957fb50d67cccf9_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroups_created_by_id_15ce94d078f5a3d2_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroups_created_by_id_15ce94d078f5a3d2_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroups_created_by_id_229d584c2c4eb8cf_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgroups_created_by_id_229d584c2c4eb8cf_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupset_ad_group_id_52bbe2cebc6d3beb_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupset_ad_group_id_52bbe2cebc6d3beb_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsour_ad_group_id_fde095cf19f3715_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsour_ad_group_id_fde095cf19f3715_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsource_source_id_367dc07cd20b0219_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_source_id_367dc07cd20b0219_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_article_ad_group_id_79aa6e718f540dfa_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_ad_group_id_79aa6e718f540dfa_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budge_budget_id_60107fc78fed66a7_fk_dash_budgetlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budge_budget_id_60107fc78fed66a7_fk_dash_budgetlineitem_id FOREIGN KEY (budget_id) REFERENCES dash_budgetlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budge_credit_id_4c0c4719ea6a6609_fk_dash_creditlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budge_credit_id_4c0c4719ea6a6609_fk_dash_creditlineitem_id FOREIGN KEY (credit_id) REFERENCES dash_creditlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgethi_created_by_id_5448d5d41591fb96_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethi_created_by_id_5448d5d41591fb96_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetli_created_by_id_6360c491f729bc2c_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetli_created_by_id_6360c491f729bc2c_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetlin_campaign_id_174e3ffc36d98c50_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlin_campaign_id_174e3ffc36d98c50_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_ca_campaign_manager_id_270df158707cea9b_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_ca_campaign_manager_id_270df158707cea9b_fk_zemauth_user_id FOREIGN KEY (campaign_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaig_modified_by_id_741ba1fd28b3509a_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaig_modified_by_id_741ba1fd28b3509a_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign__campaign_id_67477650acd7cd60_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign__campaign_id_67477650acd7cd60_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign__campaign_id_7992ef4e07158559_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign__campaign_id_7992ef4e07158559_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_account_id_46fc75bd4e25459c_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_account_id_46fc75bd4e25459c_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_created_by_id_553e282add87981d_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaign_created_by_id_553e282add87981d_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_created_by_id_5699e985b5c3ea62_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignbudgetsettings
    ADD CONSTRAINT dash_campaign_created_by_id_5699e985b5c3ea62_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_created_by_id_6a53d8a794711535_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaign_created_by_id_6a53d8a794711535_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_created_by_id_7471c5d0e929afe7_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue
    ADD CONSTRAINT dash_campaign_created_by_id_7471c5d0e929afe7_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_groups_group_id_ad705f42cbaaa7e_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_group_id_ad705f42cbaaa7e_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_users_user_id_540cb488f2a28984_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_user_id_540cb488f2a28984_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaignb_campaign_id_299670a3fe84749a_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignbudgetsettings
    ADD CONSTRAINT dash_campaignb_campaign_id_299670a3fe84749a_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigng_campaign_id_6f0236b0015e2859_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigng_campaign_id_6f0236b0015e2859_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigns_campaign_id_50afcf78e5f21307_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaigns_campaign_id_50afcf78e5f21307_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conten_content_ad_id_39eb0c55cab2148f_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_conten_content_ad_id_39eb0c55cab2148f_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentad_ad_group_id_6fade00c62b7e3ba_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_ad_group_id_6fade00c62b7e3ba_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentad_batch_id_27604bfe91608fc4_fk_dash_uploadbatch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_batch_id_27604bfe91608fc4_fk_dash_uploadbatch_id FOREIGN KEY (batch_id) REFERENCES dash_uploadbatch(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentadsour_source_id_63078da0e043aaed_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsour_source_id_63078da0e043aaed_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conve_pixel_id_31488bb522a9f7e2_fk_dash_conversionpixel_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conve_pixel_id_31488bb522a9f7e2_fk_dash_conversionpixel_id FOREIGN KEY (pixel_id) REFERENCES dash_conversionpixel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversio_campaign_id_552bc690dfe14873_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversio_campaign_id_552bc690dfe14873_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversionpi_account_id_41a77fbfb3829d5_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpi_account_id_41a77fbfb3829d5_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_credit_credit_id_6b73a9aec988def_fk_dash_creditlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credit_credit_id_6b73a9aec988def_fk_dash_creditlineitem_id FOREIGN KEY (credit_id) REFERENCES dash_creditlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_credithi_created_by_id_667cab4e545ddbee_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithi_created_by_id_667cab4e545ddbee_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditli_created_by_id_6e725d0a4c595130_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditli_created_by_id_6e725d0a4c595130_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditlinei_account_id_13334cb7c84c0fac_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlinei_account_id_13334cb7c84c0fac_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_defaultsource_source_id_318197d72ec0e837_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsource_source_id_318197d72ec0e837_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_demoa_demo_ad_group_id_1380f66b06619d55_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoa_demo_ad_group_id_1380f66b06619d55_fk_dash_adgroup_id FOREIGN KEY (demo_ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_demoa_real_ad_group_id_38bd1d4d2827da1a_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demoadgrouprealadgroup
    ADD CONSTRAINT dash_demoa_real_ad_group_id_38bd1d4d2827da1a_fk_dash_adgroup_id FOREIGN KEY (real_ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_e_exportreport_id_67cc3959ababbad4_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_e_exportreport_id_67cc3959ababbad4_fk_dash_exportreport_id FOREIGN KEY (exportreport_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportre_created_by_id_100829644781b092_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportre_created_by_id_100829644781b092_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportrepo_ad_group_id_24f2b69d5e01772b_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportrepo_ad_group_id_24f2b69d5e01772b_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportrepo_campaign_id_273cadee8c0072a_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportrepo_campaign_id_273cadee8c0072a_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportrepor_account_id_6b4cc459f095d3fe_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportrepor_account_id_6b4cc459f095d3fe_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport__source_id_429cbee48898cd97_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport__source_id_429cbee48898cd97_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_gaanalytics_account_id_65ee0ea9662729cf_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_gaanalyticsaccount
    ADD CONSTRAINT dash_gaanalytics_account_id_65ee0ea9662729cf_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisher_campaign_id_16a8dc1fe68bbc1d_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisher_campaign_id_16a8dc1fe68bbc1d_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherb_ad_group_id_6412ac4e598a7b58_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherb_ad_group_id_6412ac4e598a7b58_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherbla_account_id_c9b1391ae20870b_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherbla_account_id_c9b1391ae20870b_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherblac_source_id_1149cc9d2d63b122_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblac_source_id_1149cc9d2d63b122_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_schedul_report_id_37efeaabd2ffe728_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_schedul_report_id_37efeaabd2ffe728_fk_dash_exportreport_id FOREIGN KEY (report_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_schedule_created_by_id_4991ebc63bf02cf6_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_schedule_created_by_id_4991ebc63bf02cf6_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sour_source_type_id_7ca32910aceeb1c0_fk_dash_sourcetype_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_sour_source_type_id_7ca32910aceeb1c0_fk_dash_sourcetype_id FOREIGN KEY (source_type_id) REFERENCES dash_sourcetype(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sourcecredent_source_id_1c3729cca986d585_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcecredentials
    ADD CONSTRAINT dash_sourcecredent_source_id_1c3729cca986d585_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useractio_campaign_id_1e0d96ec4450dbac_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractio_campaign_id_1e0d96ec4450dbac_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useractio_created_by_id_ff030e12e39bcd0_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractio_created_by_id_ff030e12e39bcd0_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useraction_ad_group_id_4e57f0a40a5bbb49_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useraction_ad_group_id_4e57f0a40a5bbb49_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_useractionl_account_id_40e5ee68dafa5dac_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_useractionlog
    ADD CONSTRAINT dash_useractionl_account_id_40e5ee68dafa5dac_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: default_account_manager_id_271d5867beea1831_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT default_account_manager_id_271d5867beea1831_fk_zemauth_user_id FOREIGN KEY (default_account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: djan_content_type_id_697914295151027a_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT djan_content_type_id_697914295151027a_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_user_id_52fdd58701c5f563_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_52fdd58701c5f563_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroup_ad_group_id_13c4a3d5e20e3c39_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroup_ad_group_id_13c4a3d5e20e3c39_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroup_ad_group_id_2001c33606fdf7b8_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroup_ad_group_id_2001c33606fdf7b8_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupgoa_source_id_7e5f33fc53b57b3d_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoa_source_id_7e5f33fc53b57b3d_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupsta_source_id_1bf5bd45989635ee_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupsta_source_id_1bf5bd45989635ee_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_article_ad_group_id_3769701ff7c08bc2_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_article_ad_group_id_3769701ff7c08bc2_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlest_article_id_7f73111ba61fbcc_fk_dash_article_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlest_article_id_7f73111ba61fbcc_fk_dash_article_id FOREIGN KEY (article_id) REFERENCES dash_article(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlesta_source_id_657629aac3307008_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlesta_source_id_657629aac3307008_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_bu_budget_id_355a21131fe7d81e_fk_dash_budgetlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatement
    ADD CONSTRAINT reports_bu_budget_id_355a21131fe7d81e_fk_dash_budgetlineitem_id FOREIGN KEY (budget_id) REFERENCES dash_budgetlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_con_content_ad_id_4bdfb131b60c230a_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_con_content_ad_id_4bdfb131b60c230a_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_con_content_ad_id_67edea839702fc89_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_con_content_ad_id_67edea839702fc89_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_con_content_ad_id_6b72ab957a316bf3_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_con_content_ad_id_6b72ab957a316bf3_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadg_source_id_7a970277294d51f7_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadg_source_id_7a970277294d51f7_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadp_source_id_62765e23e38ee28d_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadp_source_id_62765e23e38ee28d_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentads_source_id_461a985b3e8b6a40_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentads_source_id_461a985b3e8b6a40_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalcon_ad_group_id_2a9a75f4336e4fa8_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalcon_ad_group_id_2a9a75f4336e4fa8_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconv_article_id_2a3e58042a67faca_fk_dash_article_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconv_article_id_2a3e58042a67faca_fk_dash_article_id FOREIGN KEY (article_id) REFERENCES dash_article(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconvers_source_id_70322d4e18d53de_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconvers_source_id_70322d4e18d53de_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_supplyrepor_source_id_a472910927d5af6_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyrepor_source_id_a472910927d5af6_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_internalgrou_group_id_64070c9185256b20_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgrou_group_id_64070c9185256b20_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_us_permission_id_77b59ab3720bfd77_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_us_permission_id_77b59ab3720bfd77_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_groups_group_id_6ba210a4daf39016_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_group_id_6ba210a4daf39016_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_groups_user_id_770269714bafc471_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_user_id_770269714bafc471_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_user_p_user_id_3bd2c96b17985b55_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_p_user_id_3bd2c96b17985b55_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

