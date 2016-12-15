--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.1
-- Dumped by pg_dump version 9.6.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

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
-- Name: actionlog_actionlog; Type: TABLE; Schema: public; Owner: -
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
-- Name: actionlog_actionlogorder; Type: TABLE; Schema: public; Owner: -
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
-- Name: auth_group; Type: TABLE; Schema: public; Owner: -
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
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: -
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
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: -
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
-- Name: automation_autopilotadgroupsourcebidcpclog; Type: TABLE; Schema: public; Owner: -
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
-- Name: automation_autopilotlog; Type: TABLE; Schema: public; Owner: -
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
    campaign_goal integer,
    goal_value numeric(10,4)
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
-- Name: automation_campaignbudgetdepletionnotification; Type: TABLE; Schema: public; Owner: -
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
-- Name: automation_campaignstoplog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE automation_campaignstoplog (
    id integer NOT NULL,
    notes text NOT NULL,
    created_dt timestamp with time zone,
    campaign_id integer NOT NULL
);


--
-- Name: automation_campaignstoplog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE automation_campaignstoplog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: automation_campaignstoplog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE automation_campaignstoplog_id_seq OWNED BY automation_campaignstoplog.id;


--
-- Name: bizwire_adgrouptargeting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE bizwire_adgrouptargeting (
    id integer NOT NULL,
    interest_targeting text NOT NULL,
    start_date date NOT NULL,
    ad_group_id integer NOT NULL
);


--
-- Name: bizwire_adgrouptargeting_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE bizwire_adgrouptargeting_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bizwire_adgrouptargeting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE bizwire_adgrouptargeting_id_seq OWNED BY bizwire_adgrouptargeting.id;


--
-- Name: dash_account; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_account (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    outbrain_marketer_id character varying(255),
    modified_by_id integer,
    agency_id integer,
    salesforce_url character varying(255)
);


--
-- Name: dash_account_allowed_sources; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_account_groups; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_account_users; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_accountsettings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_accountsettings (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    archived boolean NOT NULL,
    changes_text text,
    account_id integer NOT NULL,
    created_by_id integer NOT NULL,
    default_account_manager_id integer,
    default_sales_representative_id integer,
    account_type integer NOT NULL
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
-- Name: dash_adgroup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_adgroup (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
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
-- Name: dash_adgroupsettings; Type: TABLE; Schema: public; Owner: -
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
    archived boolean NOT NULL,
    display_url character varying(25) NOT NULL,
    brand_name character varying(25) NOT NULL,
    description character varying(140) NOT NULL,
    call_to_action character varying(25) NOT NULL,
    ad_group_name character varying(127) NOT NULL,
    changes_text text,
    ad_group_id integer NOT NULL,
    created_by_id integer,
    autopilot_daily_budget numeric(10,4),
    autopilot_state integer,
    retargeting_ad_groups text NOT NULL,
    system_user smallint,
    landing_mode boolean NOT NULL,
    exclusion_retargeting_ad_groups text NOT NULL,
    bluekai_targeting text NOT NULL,
    exclusion_interest_targeting text NOT NULL,
    interest_targeting text NOT NULL,
    notes text NOT NULL,
    redirect_javascript text NOT NULL,
    redirect_pixel_urls text NOT NULL,
    audience_targeting text NOT NULL,
    exclusion_audience_targeting text NOT NULL,
    b1_sources_group_daily_budget numeric(10,4) NOT NULL,
    b1_sources_group_enabled boolean NOT NULL,
    b1_sources_group_state integer NOT NULL,
    dayparting text NOT NULL,
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
-- Name: dash_adgroupsource; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_adgroupsourcesettings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_adgroupsourcesettings (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    cpc_cc numeric(10,4),
    daily_budget_cc numeric(10,4),
    ad_group_source_id integer,
    created_by_id integer,
    landing_mode boolean NOT NULL,
    system_user smallint,
    CONSTRAINT dash_adgroupsourcesettings_system_user_check CHECK ((system_user >= 0))
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
-- Name: dash_adgroupsourcestate; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_agency; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_agency (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    modified_by_id integer NOT NULL,
    sales_representative_id integer,
    default_account_type integer NOT NULL
);


--
-- Name: dash_agency_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_agency_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_agency_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_agency_id_seq OWNED BY dash_agency.id;


--
-- Name: dash_agency_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_agency_users (
    id integer NOT NULL,
    agency_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: dash_agency_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_agency_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_agency_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_agency_users_id_seq OWNED BY dash_agency_users.id;


--
-- Name: dash_article; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_audience; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_audience (
    id integer NOT NULL,
    ttl smallint NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    pixel_id integer NOT NULL,
    name character varying(127) NOT NULL,
    archived boolean NOT NULL,
    created_by_id integer NOT NULL,
    CONSTRAINT dash_audience_ttl_check CHECK ((ttl >= 0))
);


--
-- Name: dash_audience_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_audience_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_audience_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_audience_id_seq OWNED BY dash_audience.id;


--
-- Name: dash_audiencerule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_audiencerule (
    id integer NOT NULL,
    type smallint NOT NULL,
    value character varying(255) NOT NULL,
    audience_id integer NOT NULL,
    CONSTRAINT dash_rule_type_check CHECK ((type >= 0))
);


--
-- Name: dash_budgethistory; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_budgetlineitem; Type: TABLE; Schema: public; Owner: -
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
    freed_cc bigint NOT NULL,
    margin numeric(5,4) NOT NULL
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
-- Name: dash_campaign; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_campaign_groups; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_campaign_users; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_campaigngoal; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_campaigngoalvalue; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_campaignsettings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_campaignsettings (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
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
    adobe_tracking_param character varying(10) NOT NULL,
    enable_adobe_tracking boolean NOT NULL,
    enable_ga_tracking boolean NOT NULL,
    ga_property_id character varying(25) NOT NULL,
    ga_tracking_type integer NOT NULL,
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
-- Name: dash_contentad; Type: TABLE; Schema: public; Owner: -
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
    label character varying(100) NOT NULL,
    image_crop character varying(25) NOT NULL,
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
-- Name: dash_contentadcandidate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_contentadcandidate (
    id integer NOT NULL,
    label text,
    url text,
    title text,
    image_url text,
    image_crop text,
    display_url text,
    brand_name text,
    description text,
    call_to_action text,
    image_id character varying(256),
    image_width integer,
    image_height integer,
    image_hash character varying(128),
    created_dt timestamp with time zone NOT NULL,
    ad_group_id integer NOT NULL,
    batch_id integer NOT NULL,
    image_status integer NOT NULL,
    url_status integer NOT NULL,
    primary_tracker_url text,
    secondary_tracker_url text,
    CONSTRAINT dash_contentadcandidate_image_height_check CHECK ((image_height >= 0)),
    CONSTRAINT dash_contentadcandidate_image_width_check CHECK ((image_width >= 0))
);


--
-- Name: dash_contentadcandidate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_contentadcandidate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_contentadcandidate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_contentadcandidate_id_seq OWNED BY dash_contentadcandidate.id;


--
-- Name: dash_contentadsource; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_conversiongoal; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_conversionpixel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_conversionpixel (
    id integer NOT NULL,
    slug character varying(32) NOT NULL,
    archived boolean NOT NULL,
    last_sync_dt timestamp with time zone,
    created_dt timestamp with time zone NOT NULL,
    account_id integer NOT NULL,
    name character varying(50) NOT NULL,
    audience_enabled boolean NOT NULL
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
-- Name: dash_credithistory; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_creditlineitem; Type: TABLE; Schema: public; Owner: -
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
    account_id integer,
    created_by_id integer,
    flat_fee_cc integer NOT NULL,
    flat_fee_end_date date,
    flat_fee_start_date date,
    agency_id integer
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
-- Name: dash_defaultsourcesettings; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_demomapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_demomapping (
    id integer NOT NULL,
    demo_account_name character varying(127) NOT NULL,
    demo_campaign_name_pool character varying(127)[] NOT NULL,
    demo_ad_group_name_pool character varying(127)[] NOT NULL,
    real_account_id integer NOT NULL
);


--
-- Name: dash_demomapping_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_demomapping_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_demomapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_demomapping_id_seq OWNED BY dash_demomapping.id;


--
-- Name: dash_emailtemplate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_emailtemplate (
    id integer NOT NULL,
    template_type smallint,
    subject character varying(255) NOT NULL,
    body text NOT NULL,
    recipients text NOT NULL,
    CONSTRAINT dash_emailtemplate_template_type_check CHECK ((template_type >= 0))
);


--
-- Name: dash_emailtemplate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_emailtemplate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_emailtemplate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_emailtemplate_id_seq OWNED BY dash_emailtemplate.id;


--
-- Name: dash_exportreport; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_exportreport (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    granularity integer NOT NULL,
    breakdown_by_day boolean NOT NULL,
    breakdown_by_source boolean NOT NULL,
    order_by character varying(20),
    additional_fields text,
    account_id integer,
    ad_group_id integer,
    campaign_id integer,
    created_by_id integer NOT NULL,
    include_model_ids boolean NOT NULL,
    filtered_account_types text NOT NULL,
    include_totals boolean NOT NULL,
    include_missing boolean NOT NULL
);


--
-- Name: dash_exportreport_filtered_agencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_exportreport_filtered_agencies (
    id integer NOT NULL,
    exportreport_id integer NOT NULL,
    agency_id integer NOT NULL
);


--
-- Name: dash_exportreport_filtered_agencies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_exportreport_filtered_agencies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_exportreport_filtered_agencies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_exportreport_filtered_agencies_id_seq OWNED BY dash_exportreport_filtered_agencies.id;


--
-- Name: dash_exportreport_filtered_sources; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_facebookaccount; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_facebookaccount (
    account_id integer NOT NULL,
    ad_account_id character varying(127),
    page_url character varying(255),
    status integer NOT NULL,
    page_id character varying(127)
);


--
-- Name: dash_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_history (
    id integer NOT NULL,
    level smallint NOT NULL,
    changes_text text NOT NULL,
    changes text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    system_user smallint,
    account_id integer,
    ad_group_id integer,
    agency_id integer,
    campaign_id integer,
    created_by_id integer,
    action_type smallint,
    CONSTRAINT dash_history_action_type_check CHECK ((action_type >= 0)),
    CONSTRAINT dash_history_level_check CHECK ((level >= 0)),
    CONSTRAINT dash_history_system_user_check CHECK ((system_user >= 0))
);


--
-- Name: dash_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_history_id_seq OWNED BY dash_history.id;


--
-- Name: dash_outbrainaccount; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_publisherblacklist; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_rule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_rule_id_seq OWNED BY dash_audiencerule.id;


--
-- Name: dash_scheduledexportreport; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_scheduledexportreport (
    id integer NOT NULL,
    name character varying(100),
    created_dt timestamp with time zone NOT NULL,
    state integer NOT NULL,
    sending_frequency integer NOT NULL,
    created_by_id integer NOT NULL,
    report_id integer NOT NULL,
    time_period integer NOT NULL,
    day_of_week integer NOT NULL
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
-- Name: dash_scheduledexportreportlog; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_scheduledexportreportrecipient; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_source; Type: TABLE; Schema: public; Owner: -
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
    default_mobile_cpc_cc numeric(10,4) NOT NULL,
    impression_trackers_count smallint NOT NULL,
    CONSTRAINT dash_source_impression_trackers_count_check CHECK ((impression_trackers_count >= 0))
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
-- Name: dash_sourcecredentials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_sourcecredentials (
    id integer NOT NULL,
    name character varying(127) NOT NULL,
    credentials text NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    source_id integer NOT NULL,
    sync_reports boolean NOT NULL
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
-- Name: dash_sourcetype; Type: TABLE; Schema: public; Owner: -
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
-- Name: dash_sourcetypepixel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_sourcetypepixel (
    id integer NOT NULL,
    url character varying(255) NOT NULL,
    source_pixel_id character varying(127) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    pixel_id integer NOT NULL,
    source_type_id integer NOT NULL
);


--
-- Name: dash_sourcetypepixel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dash_sourcetypepixel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dash_sourcetypepixel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dash_sourcetypepixel_id_seq OWNED BY dash_sourcetypepixel.id;


--
-- Name: dash_uploadbatch; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dash_uploadbatch (
    id integer NOT NULL,
    name character varying(1024) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    status integer NOT NULL,
    ad_group_id integer,
    original_filename character varying(1024),
    default_brand_name text,
    default_call_to_action text,
    default_description text,
    default_display_url text,
    default_image_crop text,
    auto_save boolean NOT NULL
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
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: -
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
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -
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
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -
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
-- Name: django_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


--
-- Name: oauth2_provider_accesstoken; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE oauth2_provider_accesstoken (
    id integer NOT NULL,
    token character varying(255) NOT NULL,
    expires timestamp with time zone NOT NULL,
    scope text NOT NULL,
    application_id integer NOT NULL,
    user_id integer
);


--
-- Name: oauth2_provider_accesstoken_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE oauth2_provider_accesstoken_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oauth2_provider_accesstoken_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE oauth2_provider_accesstoken_id_seq OWNED BY oauth2_provider_accesstoken.id;


--
-- Name: oauth2_provider_application; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE oauth2_provider_application (
    id integer NOT NULL,
    client_id character varying(100) NOT NULL,
    redirect_uris text NOT NULL,
    client_type character varying(32) NOT NULL,
    authorization_grant_type character varying(32) NOT NULL,
    client_secret character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    user_id integer NOT NULL,
    skip_authorization boolean NOT NULL
);


--
-- Name: oauth2_provider_application_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE oauth2_provider_application_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oauth2_provider_application_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE oauth2_provider_application_id_seq OWNED BY oauth2_provider_application.id;


--
-- Name: oauth2_provider_grant; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE oauth2_provider_grant (
    id integer NOT NULL,
    code character varying(255) NOT NULL,
    expires timestamp with time zone NOT NULL,
    redirect_uri character varying(255) NOT NULL,
    scope text NOT NULL,
    application_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: oauth2_provider_grant_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE oauth2_provider_grant_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oauth2_provider_grant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE oauth2_provider_grant_id_seq OWNED BY oauth2_provider_grant.id;


--
-- Name: oauth2_provider_refreshtoken; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE oauth2_provider_refreshtoken (
    id integer NOT NULL,
    token character varying(255) NOT NULL,
    access_token_id integer NOT NULL,
    application_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: oauth2_provider_refreshtoken_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE oauth2_provider_refreshtoken_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oauth2_provider_refreshtoken_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE oauth2_provider_refreshtoken_id_seq OWNED BY oauth2_provider_refreshtoken.id;


--
-- Name: reports_adgroupgoalconversionstats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_adgroupstats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_articlestats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_budgetdailystatement; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE reports_budgetdailystatement (
    id integer NOT NULL,
    date date NOT NULL,
    media_spend_nano bigint NOT NULL,
    data_spend_nano bigint NOT NULL,
    license_fee_nano bigint NOT NULL,
    budget_id integer NOT NULL,
    margin_nano bigint NOT NULL
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
-- Name: reports_budgetdailystatementk1; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE reports_budgetdailystatementk1 (
    id integer NOT NULL,
    date date NOT NULL,
    media_spend_nano bigint NOT NULL,
    data_spend_nano bigint NOT NULL,
    license_fee_nano bigint NOT NULL,
    budget_id integer NOT NULL
);


--
-- Name: reports_budgetdailystatementk1_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE reports_budgetdailystatementk1_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_budgetdailystatementk1_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE reports_budgetdailystatementk1_id_seq OWNED BY reports_budgetdailystatementk1.id;


--
-- Name: reports_contentadgoalconversionstats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_contentadpostclickstats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_contentadstats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_goalconversionstats; Type: TABLE; Schema: public; Owner: -
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
-- Name: reports_supplyreportrecipient; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE reports_supplyreportrecipient (
    id integer NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    email character varying(255) NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    modified_dt timestamp with time zone NOT NULL,
    source_id integer NOT NULL,
    publishers_report boolean NOT NULL
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
-- Name: restapi_reportjob; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE restapi_reportjob (
    id integer NOT NULL,
    created_dt timestamp with time zone NOT NULL,
    status integer NOT NULL,
    query text NOT NULL,
    result text,
    user_id integer
);


--
-- Name: restapi_reportjob_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE restapi_reportjob_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: restapi_reportjob_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE restapi_reportjob_id_seq OWNED BY restapi_reportjob.id;


--
-- Name: zemauth_internalgroup; Type: TABLE; Schema: public; Owner: -
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
-- Name: zemauth_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE zemauth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(30),
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    is_test_user boolean NOT NULL
);


--
-- Name: zemauth_user_groups; Type: TABLE; Schema: public; Owner: -
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
-- Name: zemauth_user_user_permissions; Type: TABLE; Schema: public; Owner: -
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
-- Name: actionlog_actionlog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog ALTER COLUMN id SET DEFAULT nextval('actionlog_actionlog_id_seq'::regclass);


--
-- Name: actionlog_actionlogorder id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlogorder ALTER COLUMN id SET DEFAULT nextval('actionlog_actionlogorder_id_seq'::regclass);


--
-- Name: auth_group id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group ALTER COLUMN id SET DEFAULT nextval('auth_group_id_seq'::regclass);


--
-- Name: auth_group_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('auth_group_permissions_id_seq'::regclass);


--
-- Name: auth_permission id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq'::regclass);


--
-- Name: automation_autopilotadgroupsourcebidcpclog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog ALTER COLUMN id SET DEFAULT nextval('automation_autopilotadgroupsourcebidcpclog_id_seq'::regclass);


--
-- Name: automation_autopilotlog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog ALTER COLUMN id SET DEFAULT nextval('automation_autopilotlog_id_seq'::regclass);


--
-- Name: automation_campaignbudgetdepletionnotification id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification ALTER COLUMN id SET DEFAULT nextval('automation_campaignbudgetdepletionnotification_id_seq'::regclass);


--
-- Name: automation_campaignstoplog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignstoplog ALTER COLUMN id SET DEFAULT nextval('automation_campaignstoplog_id_seq'::regclass);


--
-- Name: bizwire_adgrouptargeting id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY bizwire_adgrouptargeting ALTER COLUMN id SET DEFAULT nextval('bizwire_adgrouptargeting_id_seq'::regclass);


--
-- Name: dash_account id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account ALTER COLUMN id SET DEFAULT nextval('dash_account_id_seq'::regclass);


--
-- Name: dash_account_allowed_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources ALTER COLUMN id SET DEFAULT nextval('dash_account_allowed_sources_id_seq'::regclass);


--
-- Name: dash_account_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups ALTER COLUMN id SET DEFAULT nextval('dash_account_groups_id_seq'::regclass);


--
-- Name: dash_account_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users ALTER COLUMN id SET DEFAULT nextval('dash_account_users_id_seq'::regclass);


--
-- Name: dash_accountsettings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings ALTER COLUMN id SET DEFAULT nextval('dash_accountsettings_id_seq'::regclass);


--
-- Name: dash_adgroup id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup ALTER COLUMN id SET DEFAULT nextval('dash_adgroup_id_seq'::regclass);


--
-- Name: dash_adgroupsettings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsettings_id_seq'::regclass);


--
-- Name: dash_adgroupsource id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsource_id_seq'::regclass);


--
-- Name: dash_adgroupsourcesettings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsourcesettings_id_seq'::regclass);


--
-- Name: dash_adgroupsourcestate id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcestate ALTER COLUMN id SET DEFAULT nextval('dash_adgroupsourcestate_id_seq'::regclass);


--
-- Name: dash_agency id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency ALTER COLUMN id SET DEFAULT nextval('dash_agency_id_seq'::regclass);


--
-- Name: dash_agency_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency_users ALTER COLUMN id SET DEFAULT nextval('dash_agency_users_id_seq'::regclass);


--
-- Name: dash_article id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_article ALTER COLUMN id SET DEFAULT nextval('dash_article_id_seq'::regclass);


--
-- Name: dash_audience id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audience ALTER COLUMN id SET DEFAULT nextval('dash_audience_id_seq'::regclass);


--
-- Name: dash_audiencerule id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audiencerule ALTER COLUMN id SET DEFAULT nextval('dash_rule_id_seq'::regclass);


--
-- Name: dash_budgethistory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory ALTER COLUMN id SET DEFAULT nextval('dash_budgethistory_id_seq'::regclass);


--
-- Name: dash_budgetlineitem id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem ALTER COLUMN id SET DEFAULT nextval('dash_budgetlineitem_id_seq'::regclass);


--
-- Name: dash_campaign id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign ALTER COLUMN id SET DEFAULT nextval('dash_campaign_id_seq'::regclass);


--
-- Name: dash_campaign_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups ALTER COLUMN id SET DEFAULT nextval('dash_campaign_groups_id_seq'::regclass);


--
-- Name: dash_campaign_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users ALTER COLUMN id SET DEFAULT nextval('dash_campaign_users_id_seq'::regclass);


--
-- Name: dash_campaigngoal id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal ALTER COLUMN id SET DEFAULT nextval('dash_campaigngoal_id_seq'::regclass);


--
-- Name: dash_campaigngoalvalue id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue ALTER COLUMN id SET DEFAULT nextval('dash_campaigngoalvalue_id_seq'::regclass);


--
-- Name: dash_campaignsettings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings ALTER COLUMN id SET DEFAULT nextval('dash_campaignsettings_id_seq'::regclass);


--
-- Name: dash_contentad id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad ALTER COLUMN id SET DEFAULT nextval('dash_contentad_id_seq'::regclass);


--
-- Name: dash_contentadcandidate id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadcandidate ALTER COLUMN id SET DEFAULT nextval('dash_contentadcandidate_id_seq'::regclass);


--
-- Name: dash_contentadsource id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource ALTER COLUMN id SET DEFAULT nextval('dash_contentadsource_id_seq'::regclass);


--
-- Name: dash_conversiongoal id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal ALTER COLUMN id SET DEFAULT nextval('dash_conversiongoal_id_seq'::regclass);


--
-- Name: dash_conversionpixel id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversionpixel ALTER COLUMN id SET DEFAULT nextval('dash_conversionpixel_id_seq'::regclass);


--
-- Name: dash_credithistory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory ALTER COLUMN id SET DEFAULT nextval('dash_credithistory_id_seq'::regclass);


--
-- Name: dash_creditlineitem id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem ALTER COLUMN id SET DEFAULT nextval('dash_creditlineitem_id_seq'::regclass);


--
-- Name: dash_defaultsourcesettings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings ALTER COLUMN id SET DEFAULT nextval('dash_defaultsourcesettings_id_seq'::regclass);


--
-- Name: dash_demomapping id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demomapping ALTER COLUMN id SET DEFAULT nextval('dash_demomapping_id_seq'::regclass);


--
-- Name: dash_emailtemplate id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_emailtemplate ALTER COLUMN id SET DEFAULT nextval('dash_emailtemplate_id_seq'::regclass);


--
-- Name: dash_exportreport id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_id_seq'::regclass);


--
-- Name: dash_exportreport_filtered_agencies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_agencies ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_filtered_agencies_id_seq'::regclass);


--
-- Name: dash_exportreport_filtered_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources ALTER COLUMN id SET DEFAULT nextval('dash_exportreport_filtered_sources_id_seq'::regclass);


--
-- Name: dash_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history ALTER COLUMN id SET DEFAULT nextval('dash_history_id_seq'::regclass);


--
-- Name: dash_outbrainaccount id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_outbrainaccount ALTER COLUMN id SET DEFAULT nextval('dash_outbrainaccount_id_seq'::regclass);


--
-- Name: dash_publisherblacklist id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist ALTER COLUMN id SET DEFAULT nextval('dash_publisherblacklist_id_seq'::regclass);


--
-- Name: dash_scheduledexportreport id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreport_id_seq'::regclass);


--
-- Name: dash_scheduledexportreportlog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportlog ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreportlog_id_seq'::regclass);


--
-- Name: dash_scheduledexportreportrecipient id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient ALTER COLUMN id SET DEFAULT nextval('dash_scheduledexportreportrecipient_id_seq'::regclass);


--
-- Name: dash_source id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source ALTER COLUMN id SET DEFAULT nextval('dash_source_id_seq'::regclass);


--
-- Name: dash_sourcecredentials id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcecredentials ALTER COLUMN id SET DEFAULT nextval('dash_sourcecredentials_id_seq'::regclass);


--
-- Name: dash_sourcetype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetype ALTER COLUMN id SET DEFAULT nextval('dash_sourcetype_id_seq'::regclass);


--
-- Name: dash_sourcetypepixel id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetypepixel ALTER COLUMN id SET DEFAULT nextval('dash_sourcetypepixel_id_seq'::regclass);


--
-- Name: dash_uploadbatch id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_uploadbatch ALTER COLUMN id SET DEFAULT nextval('dash_uploadbatch_id_seq'::regclass);


--
-- Name: django_admin_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq'::regclass);


--
-- Name: django_content_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq'::regclass);


--
-- Name: django_migrations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq'::regclass);


--
-- Name: oauth2_provider_accesstoken id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_accesstoken ALTER COLUMN id SET DEFAULT nextval('oauth2_provider_accesstoken_id_seq'::regclass);


--
-- Name: oauth2_provider_application id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_application ALTER COLUMN id SET DEFAULT nextval('oauth2_provider_application_id_seq'::regclass);


--
-- Name: oauth2_provider_grant id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_grant ALTER COLUMN id SET DEFAULT nextval('oauth2_provider_grant_id_seq'::regclass);


--
-- Name: oauth2_provider_refreshtoken id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_refreshtoken ALTER COLUMN id SET DEFAULT nextval('oauth2_provider_refreshtoken_id_seq'::regclass);


--
-- Name: reports_adgroupgoalconversionstats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_adgroupgoalconversionstats_id_seq'::regclass);


--
-- Name: reports_adgroupstats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats ALTER COLUMN id SET DEFAULT nextval('reports_adgroupstats_id_seq'::regclass);


--
-- Name: reports_articlestats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats ALTER COLUMN id SET DEFAULT nextval('reports_articlestats_id_seq'::regclass);


--
-- Name: reports_budgetdailystatement id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatement ALTER COLUMN id SET DEFAULT nextval('reports_budgetdailystatement_id_seq'::regclass);


--
-- Name: reports_budgetdailystatementk1 id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatementk1 ALTER COLUMN id SET DEFAULT nextval('reports_budgetdailystatementk1_id_seq'::regclass);


--
-- Name: reports_contentadgoalconversionstats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadgoalconversionstats_id_seq'::regclass);


--
-- Name: reports_contentadpostclickstats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadpostclickstats_id_seq'::regclass);


--
-- Name: reports_contentadstats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats ALTER COLUMN id SET DEFAULT nextval('reports_contentadstats_id_seq'::regclass);


--
-- Name: reports_goalconversionstats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats ALTER COLUMN id SET DEFAULT nextval('reports_goalconversionstats_id_seq'::regclass);


--
-- Name: reports_supplyreportrecipient id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_supplyreportrecipient ALTER COLUMN id SET DEFAULT nextval('reports_supplyreportrecipient_id_seq'::regclass);


--
-- Name: restapi_reportjob id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY restapi_reportjob ALTER COLUMN id SET DEFAULT nextval('restapi_reportjob_id_seq'::regclass);


--
-- Name: zemauth_internalgroup id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_internalgroup ALTER COLUMN id SET DEFAULT nextval('zemauth_internalgroup_id_seq'::regclass);


--
-- Name: zemauth_user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user ALTER COLUMN id SET DEFAULT nextval('zemauth_user_id_seq'::regclass);


--
-- Name: zemauth_user_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups ALTER COLUMN id SET DEFAULT nextval('zemauth_user_groups_id_seq'::regclass);


--
-- Name: zemauth_user_user_permissions id; Type: DEFAULT; Schema: public; Owner: -
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
19	Can add agency	7	add_agency
20	Can change agency	7	change_agency
21	Can delete agency	7	delete_agency
22	Can add account	8	add_account
23	Can change account	8	change_account
24	Can delete account	8	delete_account
25	All new accounts are automatically added to group.	8	group_account_automatically_add
26	Can add campaign	9	add_campaign
27	Can change campaign	9	change_campaign
28	Can delete campaign	9	delete_campaign
29	Can add account settings	10	add_accountsettings
30	Can change account settings	10	change_accountsettings
31	Can delete account settings	10	delete_accountsettings
32	Can add campaign settings	11	add_campaignsettings
33	Can change campaign settings	11	change_campaignsettings
34	Can delete campaign settings	11	delete_campaignsettings
35	Can add campaign goal	12	add_campaigngoal
36	Can change campaign goal	12	change_campaigngoal
37	Can delete campaign goal	12	delete_campaigngoal
38	Can add campaign goal value	13	add_campaigngoalvalue
39	Can change campaign goal value	13	change_campaigngoalvalue
40	Can delete campaign goal value	13	delete_campaigngoalvalue
41	Can add Source Type	14	add_sourcetype
42	Can change Source Type	14	change_sourcetype
43	Can delete Source Type	14	delete_sourcetype
44	Can add source	15	add_source
45	Can change source	15	change_source
46	Can delete source	15	delete_source
47	Can add source credentials	16	add_sourcecredentials
48	Can change source credentials	16	change_sourcecredentials
49	Can delete source credentials	16	delete_sourcecredentials
50	Can add default source settings	17	add_defaultsourcesettings
51	Can change default source settings	17	change_defaultsourcesettings
52	Can delete default source settings	17	delete_defaultsourcesettings
53	Can add ad group	18	add_adgroup
54	Can change ad group	18	change_adgroup
55	Can delete ad group	18	delete_adgroup
56	Can add ad group source	19	add_adgroupsource
57	Can change ad group source	19	change_adgroupsource
58	Can delete ad group source	19	delete_adgroupsource
59	Can add ad group settings	20	add_adgroupsettings
60	Can change ad group settings	20	change_adgroupsettings
61	Can delete ad group settings	20	delete_adgroupsettings
62	Can view settings in dashboard.	20	settings_view
63	Can add ad group source state	21	add_adgroupsourcestate
64	Can change ad group source state	21	change_adgroupsourcestate
65	Can delete ad group source state	21	delete_adgroupsourcestate
66	Can add ad group source settings	22	add_adgroupsourcesettings
67	Can change ad group source settings	22	change_adgroupsourcesettings
68	Can delete ad group source settings	22	delete_adgroupsourcesettings
69	Can add upload batch	23	add_uploadbatch
70	Can change upload batch	23	change_uploadbatch
71	Can delete upload batch	23	delete_uploadbatch
72	Can add content ad	24	add_contentad
73	Can change content ad	24	change_contentad
74	Can delete content ad	24	delete_contentad
75	Can add content ad source	25	add_contentadsource
76	Can change content ad source	25	change_contentadsource
77	Can delete content ad source	25	delete_contentadsource
78	Can add content ad candidate	26	add_contentadcandidate
79	Can change content ad candidate	26	change_contentadcandidate
80	Can delete content ad candidate	26	delete_contentadcandidate
81	Can add article	27	add_article
82	Can change article	27	change_article
83	Can delete article	27	delete_article
84	Can add conversion pixel	28	add_conversionpixel
85	Can change conversion pixel	28	change_conversionpixel
86	Can delete conversion pixel	28	delete_conversionpixel
87	Can add conversion goal	29	add_conversiongoal
88	Can change conversion goal	29	change_conversiongoal
89	Can delete conversion goal	29	delete_conversiongoal
93	Can add demo mapping	31	add_demomapping
94	Can change demo mapping	31	change_demomapping
95	Can delete demo mapping	31	delete_demomapping
96	Can add publisher blacklist	32	add_publisherblacklist
97	Can change publisher blacklist	32	change_publisherblacklist
98	Can delete publisher blacklist	32	delete_publisherblacklist
99	Can add credit line item	33	add_creditlineitem
100	Can change credit line item	33	change_creditlineitem
101	Can delete credit line item	33	delete_creditlineitem
102	Can add budget line item	34	add_budgetlineitem
103	Can change budget line item	34	change_budgetlineitem
104	Can delete budget line item	34	delete_budgetlineitem
105	Can add credit history	35	add_credithistory
106	Can change credit history	35	change_credithistory
107	Can delete credit history	35	delete_credithistory
108	Can add budget history	36	add_budgethistory
109	Can change budget history	36	change_budgethistory
110	Can delete budget history	36	delete_budgethistory
111	Can add export report	37	add_exportreport
112	Can change export report	37	change_exportreport
113	Can delete export report	37	delete_exportreport
114	Can add scheduled export report	38	add_scheduledexportreport
115	Can change scheduled export report	38	change_scheduledexportreport
116	Can delete scheduled export report	38	delete_scheduledexportreport
117	Can add scheduled export report recipient	39	add_scheduledexportreportrecipient
118	Can change scheduled export report recipient	39	change_scheduledexportreportrecipient
119	Can delete scheduled export report recipient	39	delete_scheduledexportreportrecipient
120	Can add scheduled export report log	40	add_scheduledexportreportlog
121	Can change scheduled export report log	40	change_scheduledexportreportlog
122	Can delete scheduled export report log	40	delete_scheduledexportreportlog
123	Can add facebook account	41	add_facebookaccount
124	Can change facebook account	41	change_facebookaccount
125	Can delete facebook account	41	delete_facebookaccount
126	Can add email template	42	add_emailtemplate
127	Can change email template	42	change_emailtemplate
128	Can delete email template	42	delete_emailtemplate
129	Can add History	43	add_history
130	Can change History	43	change_history
131	Can delete History	43	delete_history
132	Can add source type pixel	44	add_sourcetypepixel
133	Can change source type pixel	44	change_sourcetypepixel
134	Can delete source type pixel	44	delete_sourcetypepixel
135	Can add audience	45	add_audience
136	Can change audience	45	change_audience
137	Can delete audience	45	delete_audience
141	Can add user	47	add_user
142	Can change user	47	change_user
143	Can delete user	47	delete_user
144	Can be chosen as sales representative.	47	campaign_settings_sales_rep
145	Can view supply dash link.	47	supply_dash_link_view
146	Can view all accounts's accounts tab.	47	all_accounts_accounts_view
147	Can view accounts's campaigns tab.	47	account_campaigns_view
148	Can view accounts's credit tab.	47	account_credit_view
149	Can add media sources.	47	ad_group_sources_add_source
150	Can view account sources view.	47	account_sources_view
151	Can view all accounts sources view.	47	all_accounts_sources_view
152	Can add campaigns.	47	account_campaigns_add_campaign
153	Can add accounts.	47	all_accounts_accounts_add_account
154	Can do campaign budget management.	47	campaign_budget_management_view
155	Can view account budget.	47	account_budget_view
156	Can view all accounts budget.	47	all_accounts_budget_view
157	Can archive or restore an entity.	47	archive_restore_entity
158	Can view unspent budget.	47	unspent_budget_view
159	Can switch to demo mode.	47	switch_to_demo_mode
160	Can view and set account access permissions.	47	account_agency_access_permissions
161	New users are added to this group.	47	group_new_user_add
162	Can download detailed report on campaign level.	47	campaign_ad_groups_detailed_report
163	Can view content ads postclick acq. metrics.	47	content_ads_postclick_acquisition
164	Can view aggregate postclick acq. metrics.	47	aggregate_postclick_acquisition
165	Can view aggregate postclick eng. metrics.	47	aggregate_postclick_engagement
166	Can view publishers postclick acq. metrics.	47	view_pubs_postclick_acquisition
167	Can see data status column in table.	47	data_status_column
168	Can see media source status on submission status popover	47	can_see_media_source_status_on_submission_popover
169	Can set subdivision targeting	47	can_set_subdivision_targeting
170	Can set media source to auto-pilot	47	can_set_media_source_to_auto_pilot
171	Automatically add media sources on ad group creation	47	add_media_sources_automatically
172	Can see intercom widget	47	has_intercom
173	Can see publishers	47	can_see_publishers
174	Can see Redshift postclick statistics	47	can_see_redshift_postclick_statistics
175	Automatic campaign stop on depleted budget applies to campaigns in this group	47	group_campaign_stop_on_budget_depleted
176	Can see publishers blacklist status	47	can_see_publisher_blacklist_status
177	Can modify publishers blacklist status	47	can_modify_publisher_blacklist_status
178	Can see account type	47	can_see_account_type
179	Can modify account type	47	can_modify_account_type
180	Can modify allowed sources on account level	47	can_modify_allowed_sources
181	Can view or modify global publishers blacklist status	47	can_access_global_publisher_blacklist_status
182	Can view or modify account and campaign publishers blacklist status	47	can_access_campaign_account_publisher_blacklist_status
183	Can see all available media sources in account settings	47	can_see_all_available_sources
184	Can view account's Account tab.	47	account_account_view
185	Can view actual costs	47	can_view_actual_costs
186	Can modify Outbrain account publisher blacklist status	47	can_modify_outbrain_account_publisher_blacklist_status
187	Can set Ad Group to Auto-Pilot (budget and CPC automation)	47	can_set_adgroup_to_auto_pilot
188	Can set ad group max cpc	47	can_set_ad_group_max_cpc
189	Can view retargeting settings	47	can_view_retargeting_settings
190	Can view flat fees in All accounts/accounts table	47	can_view_flat_fees
191	Can control ad group state in Campaign / Ad Groups table	47	can_control_ad_group_state_in_table
192	Can see and manage campaign goals	47	can_see_campaign_goals
193	Can see projections	47	can_see_projections
194	Can see Account Manager and Sales Representative in accounts table.	47	can_see_managers_in_accounts_table
195	Can see Campaign Manager in campaigns table.	47	can_see_managers_in_campaigns_table
196	Can show or hide chart	47	can_hide_chart
197	Can access info box on all accounts level	47	can_access_all_accounts_infobox
198	Can view aggregate campaign goal optimisation metrics	47	campaign_goal_optimization
199	Can view goal performance information	47	campaign_goal_performance
200	Can include model ids in reports	47	can_include_model_ids_in_reports
201	Has Supporthero snippet	47	has_supporthero
202	Can filter sources through sources table	47	can_filter_sources_through_table
203	Can view agency column in tables.	47	can_view_account_agency_information
204	Can view and set account sales representative on account settings tab.	47	can_set_account_sales_representative
205	Can see and modify account name on account settings tab.	47	can_modify_account_name
206	Can see and modify facebook page.	47	can_modify_facebook_page
207	Can view and set account manager on account settings tab.	47	can_modify_account_manager
208	Can view accounts history tab.	47	account_history_view
209	Hide old table on all accounts, account and campaign level.	47	hide_old_table_on_all_accounts_account_campaign_level
210	Hide old table on ad group level.	47	hide_old_table_on_ad_group_level
211	Can access table breakdowns feature on all accounts, account and campaign level.	47	can_access_table_breakdowns_feature
212	Can access table breakdowns feature on ad group level.	47	can_access_table_breakdowns_feature_on_ad_group_level
213	Can access table breakdowns feature on ad group level on publishers tab.	47	can_access_table_breakdowns_feature_on_ad_group_level_publishers
214	Can view sidetabs.	47	can_view_sidetabs
215	Can view content insights side tab on campaign level.	47	can_view_campaign_content_insights_side_tab
216	Can view and set campaign manager on campaign settings tab.	47	can_modify_campaign_manager
217	Can view and set campaign IAB category on campaign settings tab.	47	can_modify_campaign_iab_category
218	Can view ad group's history tab.	47	ad_group_history_view
219	Can view campaign's history tab.	47	campaign_history_view
220	Can view history from new history models.	47	can_view_new_history_backend
221	Can request demo v3.	47	can_request_demo_v3
222	Can set GA API tracking.	47	can_set_ga_api_tracking
223	Can filter by agency	47	can_filter_by_agency
224	Can filter by account type	47	can_filter_by_account_type
225	Can access info box on all accounts agency level	47	can_access_agency_infobox
226	User can define margin in budget line item.	47	can_manage_agency_margin
227	User can view margin in budget tab and view margin columns in tables and reports.	47	can_view_agency_margin
228	User can view platform costs broken down into media, data and fee.	47	can_view_platform_cost_breakdown
229	User can view breakdowns by delivery.	47	can_view_breakdown_by_delivery
230	User can manage custom audiences.	47	account_custom_audiences_view
231	User can target custom audiences.	47	can_target_custom_audiences
232	User can set time period when creating scheduled reports	47	can_set_time_period_in_scheduled_reports
233	User can set day of week when creating scheduled reports	47	can_set_day_of_week_in_scheduled_reports
234	User can see agency managers under access permissions	47	can_see_agency_managers_under_access_permissions
235	User can promote agency managers on account settings tab	47	can_promote_agency_managers
236	Agency managers are added to this group when promoted	47	group_agency_manager_add
237	User can set agency for account	47	can_set_agency_for_account
238	User can use single content ad upload	47	can_use_single_ad_upload
239	User can toggle between old and new design	47	can_toggle_new_design
240	User can see new header	47	can_see_new_header
241	Partially update upload candidate fields	47	can_use_partial_updates_in_upload
242	User can use their own images in upload	47	can_use_own_images_in_upload
243	User can see all users when selecting account or campaign manager	47	can_see_all_users_for_managers
244	Can add internal group	48	add_internalgroup
245	Can change internal group	48	change_internalgroup
246	Can delete internal group	48	delete_internalgroup
247	Can add action log order	49	add_actionlogorder
248	Can change action log order	49	change_actionlogorder
249	Can delete action log order	49	delete_actionlogorder
250	Can add action log	50	add_actionlog
251	Can change action log	50	change_actionlog
252	Can delete action log	50	delete_actionlog
253	Can view manual ActionLog actions	50	manual_view
254	Can acknowledge manual ActionLog actions	50	manual_acknowledge
255	Can add article stats	51	add_articlestats
256	Can change article stats	51	change_articlestats
257	Can delete article stats	51	delete_articlestats
258	Can add goal conversion stats	52	add_goalconversionstats
259	Can change goal conversion stats	52	change_goalconversionstats
260	Can delete goal conversion stats	52	delete_goalconversionstats
261	Can add ad group stats	53	add_adgroupstats
262	Can change ad group stats	53	change_adgroupstats
263	Can delete ad group stats	53	delete_adgroupstats
264	Can add ad group goal conversion stats	54	add_adgroupgoalconversionstats
265	Can change ad group goal conversion stats	54	change_adgroupgoalconversionstats
266	Can delete ad group goal conversion stats	54	delete_adgroupgoalconversionstats
267	Can add content ad stats	55	add_contentadstats
268	Can change content ad stats	55	change_contentadstats
269	Can delete content ad stats	55	delete_contentadstats
270	Can add supply report recipient	56	add_supplyreportrecipient
271	Can change supply report recipient	56	change_supplyreportrecipient
272	Can delete supply report recipient	56	delete_supplyreportrecipient
273	Can add content ad postclick stats	57	add_contentadpostclickstats
274	Can change content ad postclick stats	57	change_contentadpostclickstats
275	Can delete content ad postclick stats	57	delete_contentadpostclickstats
276	Can add content ad goal conversion stats	58	add_contentadgoalconversionstats
277	Can change content ad goal conversion stats	58	change_contentadgoalconversionstats
278	Can delete content ad goal conversion stats	58	delete_contentadgoalconversionstats
279	Can add budget daily statement	59	add_budgetdailystatement
280	Can change budget daily statement	59	change_budgetdailystatement
281	Can delete budget daily statement	59	delete_budgetdailystatement
282	Can add budget daily statement k1	60	add_budgetdailystatementk1
283	Can change budget daily statement k1	60	change_budgetdailystatementk1
284	Can delete budget daily statement k1	60	delete_budgetdailystatementk1
285	Can add campaign budget depletion notification	61	add_campaignbudgetdepletionnotification
286	Can change campaign budget depletion notification	61	change_campaignbudgetdepletionnotification
287	Can delete campaign budget depletion notification	61	delete_campaignbudgetdepletionnotification
288	Can add autopilot ad group source bid cpc log	62	add_autopilotadgroupsourcebidcpclog
289	Can change autopilot ad group source bid cpc log	62	change_autopilotadgroupsourcebidcpclog
290	Can delete autopilot ad group source bid cpc log	62	delete_autopilotadgroupsourcebidcpclog
291	Can add autopilot log	63	add_autopilotlog
292	Can change autopilot log	63	change_autopilotlog
293	Can delete autopilot log	63	delete_autopilotlog
294	Can add campaign stop log	64	add_campaignstoplog
295	Can change campaign stop log	64	change_campaignstoplog
296	Can delete campaign stop log	64	delete_campaignstoplog
297	Can add audience rule	65	add_audiencerule
298	Can change audience rule	65	change_audiencerule
299	Can delete audience rule	65	delete_audiencerule
300	Can add report job	66	add_reportjob
301	Can change report job	66	change_reportjob
302	Can delete report job	66	delete_reportjob
303	User can see new filter selector	47	can_see_new_filter_selector
304	User can see new theme	47	can_see_new_theme
305	Can include totals in reports	47	can_include_totals_in_reports
306	Can view additional targeting	47	can_view_additional_targeting
307	User can do bulk actions on all levels	47	bulk_actions_on_all_levels
308	User can see landing mode alerts above tables	47	can_see_landing_mode_alerts
309	User can manage OAuth2 applications	47	can_manage_oauth2_apps
310	User can use the REST API	47	can_use_restapi
311	User can see new settings	47	can_see_new_settings
312	User can generate publisher reports	47	can_access_publisher_reports
313	User can see RTB Sources grouped as one	47	can_see_rtb_sources_as_one
314	User can set and see interest targeting settings	47	can_set_interest_targeting
315	Can add application	67	add_application
316	Can change application	67	change_application
317	Can delete application	67	delete_application
318	Can add grant	68	add_grant
319	Can change grant	68	change_grant
320	Can delete grant	68	delete_grant
321	Can add access token	69	add_accesstoken
322	Can change access token	69	change_accesstoken
323	Can delete access token	69	delete_accesstoken
324	Can add refresh token	70	add_refreshtoken
325	Can change refresh token	70	change_refreshtoken
326	Can delete refresh token	70	delete_refreshtoken
327	Can add ad group targeting	71	add_adgrouptargeting
328	Can change ad group targeting	71	change_adgrouptargeting
329	Can delete ad group targeting	71	delete_adgrouptargeting
\.


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('auth_permission_id_seq', 329, true);


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

COPY automation_autopilotlog (id, created_dt, yesterdays_clicks, yesterdays_spend_cc, previous_cpc_cc, new_cpc_cc, previous_daily_budget, new_daily_budget, budget_comments, ad_group_id, ad_group_source_id, autopilot_type, cpc_comments, campaign_goal, goal_value) FROM stdin;
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
-- Data for Name: automation_campaignstoplog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY automation_campaignstoplog (id, notes, created_dt, campaign_id) FROM stdin;
\.


--
-- Name: automation_campaignstoplog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('automation_campaignstoplog_id_seq', 1, false);


--
-- Data for Name: bizwire_adgrouptargeting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY bizwire_adgrouptargeting (id, interest_targeting, start_date, ad_group_id) FROM stdin;
\.


--
-- Name: bizwire_adgrouptargeting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('bizwire_adgrouptargeting_id_seq', 1, false);


--
-- Data for Name: dash_account; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_account (id, name, created_dt, modified_dt, outbrain_marketer_id, modified_by_id, agency_id, salesforce_url) FROM stdin;
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

COPY dash_accountsettings (id, name, created_dt, archived, changes_text, account_id, created_by_id, default_account_manager_id, default_sales_representative_id, account_type) FROM stdin;
\.


--
-- Name: dash_accountsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_accountsettings_id_seq', 1, false);


--
-- Data for Name: dash_adgroup; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroup (id, name, created_dt, modified_dt, campaign_id, modified_by_id) FROM stdin;
\.


--
-- Name: dash_adgroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_adgroup_id_seq', 1, false);


--
-- Data for Name: dash_adgroupsettings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_adgroupsettings (id, created_dt, state, start_date, end_date, cpc_cc, daily_budget_cc, target_devices, target_regions, tracking_code, archived, display_url, brand_name, description, call_to_action, ad_group_name, changes_text, ad_group_id, created_by_id, autopilot_daily_budget, autopilot_state, retargeting_ad_groups, system_user, landing_mode, exclusion_retargeting_ad_groups, bluekai_targeting, exclusion_interest_targeting, interest_targeting, notes, redirect_javascript, redirect_pixel_urls, audience_targeting, exclusion_audience_targeting, b1_sources_group_daily_budget, b1_sources_group_enabled, b1_sources_group_state, dayparting) FROM stdin;
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

COPY dash_adgroupsourcesettings (id, created_dt, state, cpc_cc, daily_budget_cc, ad_group_source_id, created_by_id, landing_mode, system_user) FROM stdin;
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
-- Data for Name: dash_agency; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_agency (id, name, created_dt, modified_dt, modified_by_id, sales_representative_id, default_account_type) FROM stdin;
\.


--
-- Name: dash_agency_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_agency_id_seq', 1, false);


--
-- Data for Name: dash_agency_users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_agency_users (id, agency_id, user_id) FROM stdin;
\.


--
-- Name: dash_agency_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_agency_users_id_seq', 1, false);


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
-- Data for Name: dash_audience; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_audience (id, ttl, created_dt, modified_dt, pixel_id, name, archived, created_by_id) FROM stdin;
\.


--
-- Name: dash_audience_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_audience_id_seq', 1, false);


--
-- Data for Name: dash_audiencerule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_audiencerule (id, type, value, audience_id) FROM stdin;
\.


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

COPY dash_budgetlineitem (id, start_date, end_date, amount, comment, created_dt, modified_dt, campaign_id, created_by_id, credit_id, freed_cc, margin) FROM stdin;
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

COPY dash_campaignsettings (id, name, created_dt, iab_category, promotion_goal, campaign_goal, goal_quantity, target_devices, target_regions, archived, changes_text, campaign_id, created_by_id, campaign_manager_id, automatic_campaign_stop, landing_mode, system_user, adobe_tracking_param, enable_adobe_tracking, enable_ga_tracking, ga_property_id, ga_tracking_type) FROM stdin;
\.


--
-- Name: dash_campaignsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_campaignsettings_id_seq', 1, false);


--
-- Data for Name: dash_contentad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_contentad (id, url, title, display_url, brand_name, description, call_to_action, image_id, image_width, image_height, image_hash, crop_areas, redirect_id, created_dt, state, archived, tracker_urls, ad_group_id, batch_id, label, image_crop) FROM stdin;
\.


--
-- Name: dash_contentad_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_contentad_id_seq', 1, false);


--
-- Data for Name: dash_contentadcandidate; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_contentadcandidate (id, label, url, title, image_url, image_crop, display_url, brand_name, description, call_to_action, image_id, image_width, image_height, image_hash, created_dt, ad_group_id, batch_id, image_status, url_status, primary_tracker_url, secondary_tracker_url) FROM stdin;
\.


--
-- Name: dash_contentadcandidate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_contentadcandidate_id_seq', 1, false);


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

COPY dash_conversionpixel (id, slug, archived, last_sync_dt, created_dt, account_id, name, audience_enabled) FROM stdin;
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

COPY dash_creditlineitem (id, start_date, end_date, amount, license_fee, status, comment, created_dt, modified_dt, account_id, created_by_id, flat_fee_cc, flat_fee_end_date, flat_fee_start_date, agency_id) FROM stdin;
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
-- Data for Name: dash_demomapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_demomapping (id, demo_account_name, demo_campaign_name_pool, demo_ad_group_name_pool, real_account_id) FROM stdin;
\.


--
-- Name: dash_demomapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_demomapping_id_seq', 1, false);


--
-- Data for Name: dash_emailtemplate; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_emailtemplate (id, template_type, subject, body, recipients) FROM stdin;
1	1	Settings change - ad group {ad_group.name}, campaign {campaign.name}, account {account.name}	Hi account manager of ad group {ad_group.name}\n\nWe'd like to notify you that {user.email} has made the following change in the settings of the ad group {ad_group.name}, campaign {campaign.name}, account {account.name}:\n\n{changes_text}\n\nPlease check {link_url} for further details.\n\nYours truly,\nZemanta\n    	
2	2	Settings change - campaign {campaign.name}, account {account.name}	Hi account manager of campaign {campaign.name}\n\nWe'd like to notify you that {user.email} has made the following change in the settings of campaign {campaign.name}, account {account.name}:\n\n{changes_text}\n\nPlease check {link_url} for further details.\n\nYours truly,\nZemanta\n    	
3	3	Settings change - campaign {campaign.name}, account {account.name}	Hi account manager of campaign {campaign.name}\n\nWe'd like to notify you that {user.email} has made the following change in the budget of campaign {campaign.name}, account {account.name}:\n\n{changes_text}\n\nPlease check {link_url} for further details.\n\nYours truly,\nZemanta\n    	
4	4	Conversion pixel added - account {account.name}	Hi default account manager of {account.name},\n\nWe'd like to notify you that {user.email} has added a conversion pixel on account {account.name}. Please check {link_url} for details.\n\nYours truly,\nZemanta\n    	
5	5	Recover Password	<p>Hi {user.first_name},</p>\n<p>You told us you forgot your password. If you really did, click here to choose a new one:</p>\n<a href="{link_url}">Choose a New Password</a>\n<p>If you didn't mean to reset your password, then you can just ignore this email; your password will not change.</p>\n<p>\nAs always, please don't hesitate to contact help@zemanta.com with any questions.\n</p>\n<p>\nThanks,<br/>\nZemanta Client Services\n</p>\n    	
6	6	Welcome to Zemanta!	<p>Hi {user.first_name},</p>\n<p>\nWelcome to Zemanta's Content DSP!\n</p>\n<p>\nWe're excited to promote your quality content across our extended network. Through our reporting dashboard, you can monitor campaign performance across multiple supply channels.\n</p>\n<p>\nClick <a href="{link_url}">here</a> to create a password to log into your Zemanta account.\n</p>\n<p>\nAs always, please don't hesitate to contact help@zemanta.com with any questions.\n</p>\n<p>\nThanks,<br/>\nZemanta Client Services\n</p>\n    	
7	7	Zemanta Report for {date}	\nHello,\n\nHere are the impressions and spend for {date}.\n\nImpressions: {impressions}\nSpend: {cost}\n\nYours truly,\nZemanta\n\n---\nThe reporting data is an estimate. Final amounts are tallied and should be invoiced per your agreement with Zemanta.\n* All times are in Eastern Standard Time (EST).\n    	
8	8	Zemanta Scheduled Report: {report_name}	Hi,\n\nPlease find attached Your {frequency} scheduled report "{report_name}" for {entity_level}{entity_name}{granularity}.\n\nYours truly,\nZemanta\n\n----------\n\nReport was scheduled by {scheduled_by}.\n    	
9	9	Campaign budget low - {campaign.name}, {account.name}	Hi account manager of {campaign.name}\n\nWe'd like to notify you that campaign {campaign.name}, {account.name} is about to run out of available budget.\n\nThe available budget remaining today is ${available_budget}, current daily cap is ${cap} and yesterday's spend was ${yesterday_spend}.\n\nPlease check {link_url} for details.\n\nYours truly,\nZemanta\n    	
10	10	Campaign stopped - {campaign.name}, {account.name}	Hi account manager of {campaign.name}\n\nWe'd like to notify you that campaign {campaign.name}, {account.name} has run out of available budget and was stopped.\n\nPlease check {link_url} for details.\n\nYours truly,\nZemanta\n    	
11	11	Campaign Autopilot Changes - {campaign.name}, {account.name}	Hi account manager of {account.name}\n\n            On the ad groups in campaign {campaign.name}, which are set to autopilot, the system made the following changes:{changes}\n\n            Please check {link_url} for details.\n\n            Yours truly,\n            Zemanta\n	
12	12	Ad Group put on Bid CPC and Daily Budgets Optimising Autopilot - {account.name}	Hi account manager of {account.name}\n\n            Bid CPC and Daily Budgets Optimising Autopilot's settings on Your ad group in campaign {campaign.name} have been changed.\n            Autopilot made the following changes:{changes}\n            - all Paused Media Sources' Daily Budgets have been set to minimum values.\n\n            Please check {link_url} for details.\n\n            Yours truly,\n            Zemanta\n	
15	16	Livestream session started	User {user.email} started a new livestream session, accesssible on: {session_url}	operations@zemanta.com, ziga.stopinsek@zemanta.com
16	17	Daily management report	Please use an email client with HTML support.	ziga.stopinsek@zemanta.com, bostjan@zemanta.com, urska.kosec@zemanta.com
17	18	Unused Outbrain accounts running out	Hi,\nthere are only {n} unused Outbrain accounts left on Z1.\n    	
18	19	Google Analytics Setup Instructions	Dear manager,\n\nthe instructions on http://help.zemanta.com/article/show/10814-realtime-google-analytics-reports_1 will walk you through the simple setup process in Zemanta One and your Google Analytics account.\n\nYours truly,\nZemanta\n    	
13	13	Campaign is switching to landing mode	Hi, campaign manager,\n\nyour campaign {campaign.name} ({account.name}) has been switched to automated landing mode because it is approaching the budget limit.\n\nPlease visit {link_url} and assign additional budget, if you don’t want campaign to be switched to the landing mode. While campaign is in landing mode, CPCs and daily budgets of media sources will not be available for any changes, to ensure accurate delivery.\n\nLearn more about landing mode: http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode.\n\nYours truly,\nZemanta	
14	14	Campaign is running out of budget	Hi, campaign manager,\n\nyour campaign {campaign.name} ({account.name}) will soon run out of budget.\n\nPlease add the budget to continue to adjust media sources settings by your needs, if you don’t want campaign to end in a few days. To do so please visit {link_url} and assign budget to your campaign.\n\nIf you don’t take any actions, system will automatically turn on the landing mode to hit your budget. While campaign is in landing mode, CPCs and daily budgets of media sources will not be available for any changes. Learn more about landing mode: http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode.\n\nYours truly,\nZemanta	
20	15	Demo is running	Hi,\n\nDemo is running.\nLog in to {url}\nu/p: regular.user+demo@zemanta.com / {password}\n\nNote: This instance will selfdestroy in 7 days\n\nYours truly,\nZemanta\n    	
19	20	Report results	Hi,\n\nYou requested a report with the following settings:\n\nAccount: {account_name}\nCampaign: {campaign_name}\nAd Group: {ad_group_name}\n\nDate range: {start_date} - {end_date}\nView: {tab_name}\nBreakdowns: {breakdown}\nColumns: {columns}\nFilters: {filters}\nTotals included: {include_totals}\n\nYou can download the report here: {link_url}.\nReport will be available for download until {expiry_date}.\n\nYours truly,\nZemanta\n    	
\.


--
-- Name: dash_emailtemplate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_emailtemplate_id_seq', 20, true);


--
-- Data for Name: dash_exportreport; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_exportreport (id, created_dt, granularity, breakdown_by_day, breakdown_by_source, order_by, additional_fields, account_id, ad_group_id, campaign_id, created_by_id, include_model_ids, filtered_account_types, include_totals, include_missing) FROM stdin;
\.


--
-- Data for Name: dash_exportreport_filtered_agencies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_exportreport_filtered_agencies (id, exportreport_id, agency_id) FROM stdin;
\.


--
-- Name: dash_exportreport_filtered_agencies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_exportreport_filtered_agencies_id_seq', 1, false);


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
-- Data for Name: dash_facebookaccount; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_facebookaccount (account_id, ad_account_id, page_url, status, page_id) FROM stdin;
\.


--
-- Data for Name: dash_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_history (id, level, changes_text, changes, created_dt, system_user, account_id, ad_group_id, agency_id, campaign_id, created_by_id, action_type) FROM stdin;
\.


--
-- Name: dash_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_history_id_seq', 1, false);


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
-- Name: dash_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_rule_id_seq', 1, false);


--
-- Data for Name: dash_scheduledexportreport; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_scheduledexportreport (id, name, created_dt, state, sending_frequency, created_by_id, report_id, time_period, day_of_week) FROM stdin;
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

COPY dash_source (id, name, tracking_slug, bidder_slug, maintenance, deprecated, created_dt, modified_dt, released, content_ad_submission_type, source_type_id, supports_retargeting, supports_retargeting_manually, default_cpc_cc, default_daily_budget_cc, default_mobile_cpc_cc, impression_trackers_count) FROM stdin;
\.


--
-- Name: dash_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_source_id_seq', 1, false);


--
-- Data for Name: dash_sourcecredentials; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_sourcecredentials (id, name, credentials, created_dt, modified_dt, source_id, sync_reports) FROM stdin;
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
-- Data for Name: dash_sourcetypepixel; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_sourcetypepixel (id, url, source_pixel_id, created_dt, modified_dt, pixel_id, source_type_id) FROM stdin;
\.


--
-- Name: dash_sourcetypepixel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_sourcetypepixel_id_seq', 1, false);


--
-- Data for Name: dash_uploadbatch; Type: TABLE DATA; Schema: public; Owner: -
--

COPY dash_uploadbatch (id, name, created_dt, status, ad_group_id, original_filename, default_brand_name, default_call_to_action, default_description, default_display_url, default_image_crop, auto_save) FROM stdin;
\.


--
-- Name: dash_uploadbatch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('dash_uploadbatch_id_seq', 1, false);


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
7	dash	agency
8	dash	account
9	dash	campaign
10	dash	accountsettings
11	dash	campaignsettings
12	dash	campaigngoal
13	dash	campaigngoalvalue
14	dash	sourcetype
15	dash	source
16	dash	sourcecredentials
17	dash	defaultsourcesettings
18	dash	adgroup
19	dash	adgroupsource
20	dash	adgroupsettings
21	dash	adgroupsourcestate
22	dash	adgroupsourcesettings
23	dash	uploadbatch
24	dash	contentad
25	dash	contentadsource
26	dash	contentadcandidate
27	dash	article
28	dash	conversionpixel
29	dash	conversiongoal
31	dash	demomapping
32	dash	publisherblacklist
33	dash	creditlineitem
34	dash	budgetlineitem
35	dash	credithistory
36	dash	budgethistory
37	dash	exportreport
38	dash	scheduledexportreport
39	dash	scheduledexportreportrecipient
40	dash	scheduledexportreportlog
41	dash	facebookaccount
42	dash	emailtemplate
43	dash	history
44	dash	sourcetypepixel
45	dash	audience
47	zemauth	user
48	zemauth	internalgroup
49	actionlog	actionlogorder
50	actionlog	actionlog
51	reports	articlestats
52	reports	goalconversionstats
53	reports	adgroupstats
54	reports	adgroupgoalconversionstats
55	reports	contentadstats
56	reports	supplyreportrecipient
57	reports	contentadpostclickstats
58	reports	contentadgoalconversionstats
59	reports	budgetdailystatement
60	reports	budgetdailystatementk1
61	automation	campaignbudgetdepletionnotification
62	automation	autopilotadgroupsourcebidcpclog
63	automation	autopilotlog
64	automation	campaignstoplog
65	dash	audiencerule
66	restapi	reportjob
67	oauth2_provider	application
68	oauth2_provider	grant
69	oauth2_provider	accesstoken
70	oauth2_provider	refreshtoken
71	bizwire	adgrouptargeting
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('django_content_type_id_seq', 71, true);


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2016-10-12 08:28:09.877102+00
2	contenttypes	0002_remove_content_type_name	2016-10-12 08:28:09.889973+00
3	auth	0001_initial	2016-10-12 08:28:09.921069+00
4	auth	0002_alter_permission_name_max_length	2016-10-12 08:28:09.928711+00
5	auth	0003_alter_user_email_max_length	2016-10-12 08:28:09.93675+00
6	auth	0004_alter_user_username_opts	2016-10-12 08:28:09.94511+00
7	auth	0005_alter_user_last_login_null	2016-10-12 08:28:09.953255+00
8	auth	0006_require_contenttypes_0002	2016-10-12 08:28:09.954643+00
9	zemauth	0001_initial	2016-10-12 08:28:09.992461+00
10	dash	0001_initial	2016-10-12 08:28:12.576189+00
11	dash	0002_auto_20151215_1353	2016-10-12 08:28:12.708943+00
12	dash	0003_auto_20151215_1353	2016-10-12 08:28:12.71985+00
13	dash	0004_auto_20151216_0950	2016-10-12 08:28:12.813262+00
14	dash	0005_budgetlineitem_freed_cc	2016-10-12 08:28:12.884168+00
15	dash	0006_auto_20151224_1036	2016-10-12 08:28:12.948194+00
16	dash	0007_auto_20151230_1007	2016-10-12 08:28:13.011362+00
17	dash	0008_remove_campaignsettings_sales_representative	2016-10-12 08:28:13.096976+00
18	dash	0009_campaignsettings_campaign_manager	2016-10-12 08:28:13.162085+00
19	dash	0008_publisherblacklist_external_id	2016-10-12 08:28:13.349163+00
20	dash	0010_merge	2016-10-12 08:28:13.350942+00
21	dash	0011_remove_campaignsettings_account_manager	2016-10-12 08:28:13.440925+00
22	dash	0012_auto_20160115_0927	2016-10-12 08:28:13.500544+00
23	dash	0013_remove_defaultsourcesettings_auto_add	2016-10-12 08:28:13.56483+00
24	dash	0014_auto_20160121_1712	2016-10-12 08:28:13.760471+00
25	dash	0015_auto_20160121_1741	2016-10-12 08:28:14.160236+00
26	dash	0016_auto_20160126_0933	2016-10-12 08:28:14.506241+00
27	dash	0017_auto_20160127_0953	2016-10-12 08:28:14.634288+00
28	dash	0018_auto_20160127_1553	2016-10-12 08:28:14.698569+00
29	dash	0019_auto_20160201_1044	2016-10-12 08:28:14.889951+00
30	dash	0020_auto_20160201_1505	2016-10-12 08:28:15.022557+00
31	dash	0021_auto_20160210_1545	2016-10-12 08:28:15.087913+00
32	dash	0021_adgroupsettings_retargeting_ad_groups	2016-10-12 08:28:15.165114+00
33	dash	0022_merge	2016-10-12 08:28:15.167178+00
34	dash	0023_auto_20160217_0908	2016-10-12 08:28:15.438057+00
35	dash	0023_auto_20160216_1207	2016-10-12 08:28:15.530755+00
36	dash	0024_merge	2016-10-12 08:28:15.532745+00
37	dash	0025_remove_account_uses_credits	2016-10-12 08:28:15.60423+00
38	dash	0025_auto_20160223_1016	2016-10-12 08:28:15.673153+00
39	dash	0026_merge	2016-10-12 08:28:15.675507+00
40	dash	0027_sourcetype_budgets_tz	2016-10-12 08:28:15.772019+00
41	dash	0028_campaign_landing_mode	2016-10-12 08:28:15.844223+00
42	dash	0029_auto_20160303_1708	2016-10-12 08:28:15.924995+00
43	dash	0030_source_supports_retargeting	2016-10-12 08:28:15.989348+00
44	dash	0031_auto_20160314_1442	2016-10-12 08:28:16.119921+00
45	dash	0032_auto_20160316_1633	2016-10-12 08:28:16.426868+00
46	dash	0033_auto_20160316_1335	2016-10-12 08:28:16.43383+00
47	dash	0032_auto_20160315_1204	2016-10-12 08:28:16.718203+00
48	dash	0034_merge	2016-10-12 08:28:16.719825+00
49	dash	0035_auto_20160318_1503	2016-10-12 08:28:16.730464+00
50	dash	0036_auto_20160321_1515	2016-10-12 08:28:17.042189+00
51	dash	0037_auto_20160321_1537	2016-10-12 08:28:17.254349+00
52	dash	0038_adgroupsettings_system_user	2016-10-12 08:28:17.423892+00
53	dash	0039_campaignsettings_system_user	2016-10-12 08:28:17.489627+00
54	dash	0040_auto_20160322_1637	2016-10-12 08:28:17.558253+00
55	dash	0041_auto_20160323_1325	2016-10-12 08:28:17.623734+00
56	dash	0042_auto_20160325_1007	2016-10-12 08:28:17.750184+00
57	dash	0043_auto_20160331_0937	2016-10-12 08:28:17.874006+00
58	dash	0043_adgroupsettings_landing_mode	2016-10-12 08:28:17.942082+00
59	dash	0044_merge	2016-10-12 08:28:17.943718+00
60	dash	0044_exportreport_include_model_ids	2016-10-12 08:28:18.012478+00
61	dash	0045_merge	2016-10-12 08:28:18.014498+00
62	dash	0046_sourcecredentials_sync_reports	2016-10-12 08:28:18.080736+00
63	dash	0047_auto_20160413_1420	2016-10-12 08:28:18.152797+00
64	dash	0046_remove_adgroupsourcesettings_autopilot_state	2016-10-12 08:28:18.319914+00
65	dash	0048_merge	2016-10-12 08:28:18.322161+00
66	dash	0047_auto_20160413_1256	2016-10-12 08:28:18.550722+00
67	dash	0049_merge	2016-10-12 08:28:18.55262+00
68	dash	0050_remove_adgroup_content_ads_tab_with_cms	2016-10-12 08:28:18.615026+00
69	dash	0051_auto_20160419_1101	2016-10-12 08:28:18.737546+00
70	dash	0052_auto_20160421_1626	2016-10-12 08:28:18.916247+00
71	dash	0052_auto_20160421_0810	2016-10-12 08:28:19.254334+00
72	dash	0053_merge	2016-10-12 08:28:19.256012+00
73	dash	0053_accountsettings_account_type	2016-10-12 08:28:19.323568+00
74	dash	0054_merge	2016-10-12 08:28:19.325343+00
75	dash	0054_auto_20160426_1517	2016-10-12 08:28:19.531688+00
76	dash	0055_merge	2016-10-12 08:28:19.534836+00
77	dash	0056_auto_20160504_1051	2016-10-12 08:28:19.63681+00
78	dash	0057_auto_20160505_1232	2016-10-12 08:28:19.70121+00
79	dash	0055_auto_20160428_1604	2016-10-12 08:28:19.804825+00
80	dash	0058_merge	2016-10-12 08:28:19.806982+00
81	dash	0057_auto_20160504_1245	2016-10-12 08:28:19.958204+00
82	dash	0059_merge	2016-10-12 08:28:19.960187+00
83	dash	0060_auto_20160513_1431	2016-10-12 08:28:20.048804+00
84	dash	0061_auto_20160520_1341	2016-10-12 08:28:20.274177+00
85	dash	0062_auto_20160524_1350	2016-10-12 08:28:20.415085+00
86	dash	0063_facebookaccount	2016-10-12 08:28:20.487072+00
87	dash	0064_auto_20160527_1547	2016-10-12 08:28:20.758648+00
88	dash	0065_auto_20160530_1513	2016-10-12 08:28:20.778932+00
89	dash	0066_auto_20160531_0838	2016-10-12 08:28:20.792071+00
90	dash	0067_auto_20160601_1344	2016-10-12 08:28:20.804187+00
91	dash	0067_auto_20160601_0910	2016-10-12 08:28:20.947566+00
92	dash	0068_merge	2016-10-12 08:28:20.949288+00
93	dash	0067_auto_20160601_0958	2016-10-12 08:28:21.028382+00
94	dash	0069_merge	2016-10-12 08:28:21.030034+00
95	dash	0069_auto_20160601_1628	2016-10-12 08:28:21.262379+00
96	dash	0070_merge	2016-10-12 08:28:21.264394+00
97	dash	0070_accounthistory_adgrouphistory_campaignhistory	2016-10-12 08:28:21.491635+00
98	dash	0071_merge	2016-10-12 08:28:21.493941+00
99	dash	0071_auto_20160607_0751	2016-10-12 08:28:21.569596+00
100	dash	0072_merge	2016-10-12 08:28:21.572516+00
101	dash	0073_auto_20160608_1318	2016-10-12 08:28:21.785146+00
102	dash	0074_auto_20160614_0941	2016-10-12 08:28:21.861131+00
103	dash	0072_auto_20160610_0844	2016-10-12 08:28:22.638764+00
104	dash	0073_auto_20160613_1013	2016-10-12 08:28:22.650218+00
105	dash	0075_merge	2016-10-12 08:28:22.652351+00
106	dash	0076_auto_20160617_1146	2016-10-12 08:28:22.80094+00
107	dash	0077_auto_20160617_1438	2016-10-12 08:28:22.94594+00
108	dash	0078_auto_20160620_0754	2016-10-12 08:28:23.019638+00
109	dash	0076_auto_20160617_1047	2016-10-12 08:28:23.259541+00
110	dash	0077_merge	2016-10-12 08:28:23.261623+00
111	dash	0079_merge	2016-10-12 08:28:23.263457+00
112	dash	0080_auto_20160621_1129	2016-10-12 08:28:23.338047+00
113	dash	0081_auto_20160621_1129	2016-10-12 08:28:23.412735+00
114	dash	0082_history_action_type	2016-10-12 08:28:23.487209+00
115	dash	0083_auto_20160622_1120	2016-10-12 08:28:23.564939+00
116	dash	0084_auto_20160624_0927	2016-10-12 08:28:23.639543+00
117	dash	0085_auto_20160624_1337	2016-10-12 08:28:23.780997+00
118	dash	0086_auto_20160630_0914	2016-10-12 08:28:25.080398+00
119	dash	0087_auto_20160630_0918	2016-10-12 08:28:25.16694+00
120	dash	0088_audience_rule	2016-10-12 08:28:25.327308+00
121	dash	0089_auto_20160704_1339	2016-10-12 08:28:25.593062+00
122	dash	0088_auto_20160701_1347	2016-10-12 08:28:25.668922+00
123	dash	0090_merge	2016-10-12 08:28:25.671044+00
124	dash	0089_merge	2016-10-12 08:28:25.672749+00
125	dash	0091_merge	2016-10-12 08:28:25.674419+00
126	dash	0092_remove_contentadcandidate_tracker_urls	2016-10-12 08:28:25.753774+00
127	dash	0093_auto_20160705_1545	2016-10-12 08:28:26.347249+00
128	dash	0092_remove_history_type	2016-10-12 08:28:26.422669+00
129	dash	0094_merge	2016-10-12 08:28:26.424255+00
130	dash	0094_auto_20160707_0802	2016-10-12 08:28:26.588716+00
131	dash	0095_merge	2016-10-12 08:28:26.590916+00
132	dash	0096_auto_20160708_0849	2016-10-12 08:28:27.523038+00
133	dash	0097_auto_20160708_1227	2016-10-12 08:28:27.62895+00
134	dash	0095_auto_20160708_1405	2016-10-12 08:28:27.855883+00
135	dash	0098_merge	2016-10-12 08:28:27.858058+00
136	dash	0099_budgetlineitem_margin	2016-10-12 08:28:28.035329+00
137	dash	0100_auto_20160720_1131	2016-10-12 08:28:28.117701+00
138	dash	0101_auto_20160720_1140	2016-10-12 08:28:28.125474+00
139	dash	0102_auto_20160720_1141	2016-10-12 08:28:28.226767+00
140	dash	0103_auto_20160720_1148	2016-10-12 08:28:28.298808+00
141	dash	0100_auto_20160725_1212	2016-10-12 08:28:28.373315+00
142	dash	0104_merge	2016-10-12 08:28:28.375113+00
143	dash	0104_auto_20160727_1225	2016-10-12 08:28:28.380781+00
144	dash	0105_merge	2016-10-12 08:28:28.382378+00
145	dash	0106_auto_20160805_0930	2016-10-12 08:28:28.415088+00
146	dash	0107_auto_20160808_0854	2016-10-12 08:28:28.565612+00
147	dash	0108_scheduledexportreport_time_period	2016-10-12 08:28:28.645033+00
148	dash	0109_time_period_data_migration	2016-10-12 08:28:28.652711+00
149	dash	0110_scheduledexportreport_day_of_week	2016-10-12 08:28:28.732383+00
150	dash	0111_auto_20160817_0904	2016-10-12 08:28:28.807084+00
151	actionlog	0001_initial	2016-10-12 08:28:29.157582+00
152	actionlog	0002_auto_20160817_0904	2016-10-12 08:28:29.319301+00
153	admin	0001_initial	2016-10-12 08:28:29.406695+00
154	admin	0002_logentry_remove_auto_add	2016-10-12 08:28:29.488306+00
155	auth	0007_alter_validators_add_error_messages	2016-10-12 08:28:29.578748+00
156	automation	0001_initial	2016-10-12 08:28:29.753859+00
157	automation	0002_autopilotlog	2016-10-12 08:28:29.950289+00
158	automation	0003_auto_20160216_1343	2016-10-12 08:28:30.351455+00
159	automation	0004_autopilotlog_campaign_goal	2016-10-12 08:28:30.439058+00
160	automation	0005_auto_20160323_1325	2016-10-12 08:28:30.52105+00
161	automation	0006_auto_20160325_1007	2016-10-12 08:28:30.605554+00
162	automation	0007_campaignstoplog	2016-10-12 08:28:30.696667+00
163	automation	0007_autopilotlog_goal_value	2016-10-12 08:28:30.897588+00
164	automation	0008_merge	2016-10-12 08:28:30.900505+00
165	automation	0009_auto_20160421_1626	2016-10-12 08:28:30.987537+00
166	automation	0009_auto_20160421_0810	2016-10-12 08:28:31.073004+00
167	automation	0010_merge	2016-10-12 08:28:31.074982+00
168	automation	0011_auto_20160504_1051	2016-10-12 08:28:31.161364+00
169	automation	0011_auto_20160426_0917	2016-10-12 08:28:31.246854+00
170	automation	0012_merge	2016-10-12 08:28:31.24868+00
171	automation	0013_auto_20160617_1146	2016-10-12 08:28:31.331948+00
172	automation	0013_auto_20160617_1047	2016-10-12 08:28:31.419937+00
173	automation	0014_merge	2016-10-12 08:28:31.422204+00
174	automation	0015_auto_20160630_0833	2016-10-12 08:28:31.508111+00
175	automation	0016_auto_20160725_1212	2016-10-12 08:28:31.594909+00
176	dash	0112_adgroupsettings_exclusion_retargeting_ad_groups	2016-10-12 08:28:31.790082+00
177	dash	0113_auto_20160823_1125	2016-10-12 08:28:32.306439+00
178	dash	0114_agency_default_account_type	2016-10-12 08:28:32.397839+00
179	dash	0115_account_salesforce_url	2016-10-12 08:28:32.489556+00
180	dash	0114_remove_audience_ad_group_settings	2016-10-12 08:28:32.585779+00
181	dash	0116_merge	2016-10-12 08:28:32.587601+00
182	dash	0116_audience_archived	2016-10-12 08:28:32.785667+00
183	dash	0117_merge	2016-10-12 08:28:32.787868+00
184	dash	0118_auto_20160901_0844	2016-10-12 08:28:33.035862+00
185	dash	0119_auto_20160905_1023	2016-10-12 08:28:33.121742+00
186	dash	0120_auto_20160907_1421	2016-10-12 08:28:34.206381+00
187	dash	0121_auto_20160907_1422	2016-10-12 08:28:34.293754+00
188	dash	0122_auto_20160909_1356	2016-10-12 08:28:34.577301+00
189	dash	0123_auto_20160913_0843	2016-10-12 08:28:35.017253+00
190	dash	0124_auto_20160913_0845	2016-10-12 08:28:35.638821+00
191	reports	0001_initial	2016-10-12 08:28:37.592056+00
192	reports	0002_auto_20151216_0839	2016-10-12 08:28:37.719824+00
193	reports	0003_auto_20160413_1400	2016-10-12 08:28:37.863634+00
194	reports	0004_auto_20160428_1604	2016-10-12 08:28:38.057496+00
195	reports	0005_budgetdailystatement_margin_nano	2016-10-12 08:28:38.158442+00
196	reports	0006_supplyreportrecipient_publishers_report	2016-10-12 08:28:38.374107+00
197	sessions	0001_initial	2016-10-12 08:28:38.387624+00
198	zemauth	0002_auto_20151218_1526	2016-10-12 08:28:38.497767+00
199	zemauth	0003_auto_20160107_1101	2016-10-12 08:28:38.596073+00
200	zemauth	0004_auto_20160125_1333	2016-10-12 08:28:38.709275+00
201	zemauth	0005_auto_20160128_1504	2016-10-12 08:28:38.834877+00
202	zemauth	0006_auto_20160201_1505	2016-10-12 08:28:38.93308+00
203	zemauth	0007_auto_20160202_0723	2016-10-12 08:28:39.028902+00
204	zemauth	0008_auto_20160203_1458	2016-10-12 08:28:39.128064+00
205	zemauth	0009_auto_20160205_1230	2016-10-12 08:28:39.330879+00
206	zemauth	0010_auto_20160211_0817	2016-10-12 08:28:39.426795+00
207	zemauth	0011_auto_20160211_1445	2016-10-12 08:28:39.524274+00
208	zemauth	0011_auto_20160211_1417	2016-10-12 08:28:39.620198+00
209	zemauth	0012_merge	2016-10-12 08:28:39.622504+00
210	zemauth	0013_auto_20160212_1456	2016-10-12 08:28:39.718982+00
211	zemauth	0014_auto_20160219_1754	2016-10-12 08:28:39.820247+00
212	zemauth	0015_auto_20160308_0740	2016-10-12 08:28:39.92216+00
213	zemauth	0016_auto_20160308_1703	2016-10-12 08:28:40.021801+00
214	zemauth	0017_user_is_test_user	2016-10-12 08:28:40.237891+00
215	zemauth	0016_auto_20160308_1224	2016-10-12 08:28:40.33654+00
216	zemauth	0018_merge	2016-10-12 08:28:40.338955+00
217	zemauth	0019_auto_20160312_2149	2016-10-12 08:28:40.446978+00
218	zemauth	0020_auto_20160330_0805	2016-10-12 08:28:40.548934+00
219	zemauth	0021_auto_20160331_1113	2016-10-12 08:28:40.647055+00
220	zemauth	0022_auto_20160404_0839	2016-10-12 08:28:40.746619+00
221	zemauth	0023_auto_20160404_1426	2016-10-12 08:28:40.848523+00
222	zemauth	0024_auto_20160414_0904	2016-10-12 08:28:40.94673+00
223	zemauth	0025_auto_20160415_1412	2016-10-12 08:28:41.043107+00
224	zemauth	0024_auto_20160413_1436	2016-10-12 08:28:41.256211+00
225	zemauth	0026_merge	2016-10-12 08:28:41.25836+00
226	zemauth	0027_auto_20160418_1410	2016-10-12 08:28:41.358225+00
227	zemauth	0028_remove_user_show_onboarding_guidance	2016-10-12 08:28:41.457871+00
228	zemauth	0028_auto_20160421_1523	2016-10-12 08:28:41.55383+00
229	zemauth	0029_merge	2016-10-12 08:28:41.556068+00
230	zemauth	0025_auto_20160418_1453	2016-10-12 08:28:41.658046+00
231	zemauth	0028_merge	2016-10-12 08:28:41.659923+00
232	zemauth	0029_auto_20160422_0805	2016-10-12 08:28:41.756506+00
233	zemauth	0030_merge	2016-10-12 08:28:41.759207+00
234	zemauth	0031_auto_20160425_1236	2016-10-12 08:28:41.860508+00
235	zemauth	0032_auto_20160425_1434	2016-10-12 08:28:41.961094+00
236	zemauth	0033_auto_20160425_1500	2016-10-12 08:28:42.172178+00
237	zemauth	0031_auto_20160425_1152	2016-10-12 08:28:42.270041+00
238	zemauth	0034_merge	2016-10-12 08:28:42.272762+00
239	zemauth	0032_auto_20160425_1443	2016-10-12 08:28:42.372713+00
240	zemauth	0035_merge	2016-10-12 08:28:42.374666+00
241	zemauth	0033_auto_20160428_1218	2016-10-12 08:28:42.472949+00
242	zemauth	0036_merge	2016-10-12 08:28:42.475225+00
243	zemauth	0037_auto_20160504_1051	2016-10-12 08:28:42.57145+00
244	zemauth	0038_auto_20160504_1535	2016-10-12 08:28:42.674942+00
245	zemauth	0039_auto_20160509_1204	2016-10-12 08:28:42.773968+00
246	zemauth	0040_auto_20160509_1315	2016-10-12 08:28:42.876593+00
247	zemauth	0041_auto_20160510_0813	2016-10-12 08:28:43.099327+00
248	zemauth	0042_auto_20160510_1315	2016-10-12 08:28:43.21862+00
249	zemauth	0043_auto_20160511_0930	2016-10-12 08:28:43.314778+00
250	zemauth	0044_auto_20160511_0938	2016-10-12 08:28:43.41364+00
251	zemauth	0045_auto_20160512_1641	2016-10-12 08:28:43.518317+00
252	zemauth	0046_auto_20160517_0922	2016-10-12 08:28:43.614882+00
253	zemauth	0047_auto_20160519_1354	2016-10-12 08:28:43.720376+00
254	zemauth	0048_auto_20160520_1341	2016-10-12 08:28:43.821912+00
255	zemauth	0049_auto_20160523_1244	2016-10-12 08:28:43.926427+00
256	zemauth	0050_auto_20160525_1544	2016-10-12 08:28:44.144163+00
257	zemauth	0051_auto_20160527_0801	2016-10-12 08:28:44.23978+00
258	zemauth	0052_auto_20160601_1344	2016-10-12 08:28:44.336195+00
259	zemauth	0053_auto_20160601_1545	2016-10-12 08:28:44.45872+00
260	zemauth	0054_auto_20160602_0821	2016-10-12 08:28:44.561091+00
261	zemauth	0055_auto_20160606_1111	2016-10-12 08:28:44.666249+00
262	zemauth	0056_auto_20160608_1549	2016-10-12 08:28:44.773096+00
263	zemauth	0056_auto_20160607_0751	2016-10-12 08:28:44.874787+00
264	zemauth	0057_merge	2016-10-12 08:28:44.876748+00
265	zemauth	0058_auto_20160610_1255	2016-10-12 08:28:45.084297+00
266	zemauth	0057_auto_20160610_1141	2016-10-12 08:28:45.178353+00
267	zemauth	0059_merge	2016-10-12 08:28:45.180164+00
268	zemauth	0060_auto_20160614_1356	2016-10-12 08:28:45.276682+00
269	zemauth	0061_auto_20160617_1146	2016-10-12 08:28:45.373042+00
270	zemauth	0062_auto_20160629_1311	2016-10-12 08:28:45.470397+00
271	zemauth	0063_auto_20160705_1545	2016-10-12 08:28:45.568205+00
272	zemauth	0064_auto_20160708_1228	2016-10-12 08:28:45.67874+00
273	zemauth	0065_auto_20160715_1457	2016-10-12 08:28:45.778385+00
274	zemauth	0066_auto_20160719_1301	2016-10-12 08:28:46.000618+00
275	zemauth	0067_auto_20160721_1136	2016-10-12 08:28:46.10043+00
276	zemauth	0068_auto_20160721_1412	2016-10-12 08:28:46.108428+00
277	zemauth	0069_auto_20160721_1427	2016-10-12 08:28:46.206895+00
278	zemauth	0070_auto_20160729_0930	2016-10-12 08:28:46.307521+00
279	zemauth	0071_auto_20160803_1156	2016-10-12 08:28:46.40847+00
280	zemauth	0072_auto_20160803_1254	2016-10-12 08:28:46.516618+00
281	zemauth	0071_auto_20160802_1532	2016-10-12 08:28:46.616832+00
282	zemauth	0073_merge	2016-10-12 08:28:46.618932+00
283	zemauth	0073_auto_20160804_1353	2016-10-12 08:28:46.718541+00
284	zemauth	0074_merge	2016-10-12 08:28:46.72091+00
285	zemauth	0075_auto_20160808_0854	2016-10-12 08:28:46.826905+00
286	zemauth	0076_auto_20160809_1005	2016-10-12 08:28:47.045434+00
287	zemauth	0077_auto_20160811_0848	2016-10-12 08:28:47.14529+00
288	zemauth	0078_auto_20160811_1524	2016-10-12 08:28:47.24722+00
289	zemauth	0077_auto_20160812_1152	2016-10-12 08:28:47.353147+00
290	zemauth	0079_merge	2016-10-12 08:28:47.355156+00
291	zemauth	0080_auto_20160817_0904	2016-10-12 08:28:47.454258+00
292	zemauth	0081_auto_20160819_1325	2016-10-12 08:28:47.557696+00
293	zemauth	0077_auto_20160810_1438	2016-10-12 08:28:47.673393+00
294	zemauth	0082_merge	2016-10-12 08:28:47.675749+00
295	zemauth	0083_auto_20160822_1248	2016-10-12 08:28:47.785451+00
296	zemauth	0082_auto_20160825_1257	2016-10-12 08:28:47.998687+00
297	zemauth	0084_merge	2016-10-12 08:28:48.000972+00
298	zemauth	0085_auto_20160829_1449	2016-10-12 08:28:48.124175+00
299	zemauth	0085_auto_20160826_1239	2016-10-12 08:28:48.23511+00
300	zemauth	0086_merge	2016-10-12 08:28:48.238259+00
301	zemauth	0087_auto_20160831_1200	2016-10-12 08:28:48.341239+00
302	zemauth	0088_auto_20160905_1057	2016-10-12 08:28:48.444087+00
303	zemauth	0089_auto_20160906_0946	2016-10-12 08:28:48.540844+00
304	zemauth	0090_auto_20160907_1502	2016-10-12 08:28:48.636721+00
305	zemauth	0091_auto_20160908_1401	2016-10-12 08:28:48.735525+00
306	zemauth	0092_auto_20160912_0755	2016-10-12 08:28:48.943136+00
307	actionlog	0003_auto_20160914_0941	2016-12-15 16:09:02.512553+00
308	actionlog	0004_auto_20160916_1324	2016-12-15 16:09:02.591694+00
309	automation	0017_auto_20161014_1205	2016-12-15 16:09:05.103246+00
310	dash	0125_exportreport_include_totals	2016-12-15 16:09:08.768266+00
311	dash	0126_ob_running_out_email	2016-12-15 16:09:08.77829+00
312	dash	0126_auto_20160916_1324	2016-12-15 16:09:08.863278+00
313	dash	0127_merge	2016-12-15 16:09:08.865531+00
314	dash	0128_add_ga_email	2016-12-15 16:09:08.875323+00
315	dash	0129_auto_20160920_0812	2016-12-15 16:09:08.886933+00
316	dash	0130_auto_20160920_1354	2016-12-15 16:09:09.417418+00
317	dash	0131_conversionpixel_outbrain_sync	2016-12-15 16:09:09.504974+00
318	dash	0131_change_landing_mode_emails_20160923_1236	2016-12-15 16:09:09.51635+00
319	dash	0132_merge	2016-12-15 16:09:09.518677+00
320	dash	0133_auto_20161004_1141	2016-12-15 16:09:09.688136+00
321	dash	0134_auto_20161007_1328	2016-12-15 16:09:10.029081+00
322	dash	0135_auto_20161007_1410	2016-12-15 16:09:10.221596+00
323	dash	0136_auto_20161014_1205	2016-12-15 16:09:11.112284+00
324	dash	0137_uploadbatch_auto_save	2016-12-15 16:09:11.200841+00
325	dash	0137_auto_20161014_1208	2016-12-15 16:09:11.447356+00
326	dash	0138_merge	2016-12-15 16:09:11.44959+00
327	dash	0139_auto_20161021_1034	2016-12-15 16:09:11.739567+00
328	dash	0140_adgroupsettings_dayparting	2016-12-15 16:09:11.829042+00
329	dash	0141_exportreport_include_missing	2016-12-15 16:09:12.023044+00
330	dash	0142_auto_20161110_1522	2016-12-15 16:09:12.034345+00
331	dash	0143_auto_20161110_1523	2016-12-15 16:09:12.042427+00
332	dash	0144_change_demo_running_email	2016-12-15 16:09:12.050201+00
333	bizwire	0001_initial	2016-12-15 16:09:12.141755+00
334	bizwire	0002_auto_20161122_1656	2016-12-15 16:09:12.223284+00
335	dash	0145_auto_20161130_1540	2016-12-15 16:09:12.231287+00
336	dash	0146_auto_20161202_1418	2016-12-15 16:09:12.241305+00
337	dash	0147_auto_20161208_0816	2016-12-15 16:09:12.399288+00
338	oauth2_provider	0001_initial	2016-12-15 16:09:12.776321+00
339	oauth2_provider	0002_08_updates	2016-12-15 16:09:13.227464+00
340	restapi	0001_initial	2016-12-15 16:09:15.78995+00
341	zemauth	0093_auto_20160915_1033	2016-12-15 16:09:25.454591+00
342	zemauth	0094_auto_20160915_1414	2016-12-15 16:09:25.562461+00
343	zemauth	0095_auto_20160922_1320	2016-12-15 16:09:25.665906+00
344	zemauth	0096_auto_20160927_0923	2016-12-15 16:09:25.772818+00
345	zemauth	0097_auto_20161004_1524	2016-12-15 16:09:25.987761+00
346	zemauth	0098_auto_20161019_0906	2016-12-15 16:09:26.086256+00
347	zemauth	0099_auto_20161028_0827	2016-12-15 16:09:26.186205+00
348	zemauth	0100_auto_20161028_1432	2016-12-15 16:09:26.286158+00
349	zemauth	0099_auto_20161024_1401	2016-12-15 16:09:26.390119+00
350	zemauth	0101_merge	2016-12-15 16:09:26.391965+00
351	zemauth	0102_auto_20161108_1308	2016-12-15 16:09:26.494332+00
352	zemauth	0103_auto_20161202_1010	2016-12-15 16:09:26.60071+00
353	zemauth	0104_auto_20161208_0816	2016-12-15 16:09:26.702415+00
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('django_migrations_id_seq', 353, true);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: oauth2_provider_accesstoken; Type: TABLE DATA; Schema: public; Owner: -
--

COPY oauth2_provider_accesstoken (id, token, expires, scope, application_id, user_id) FROM stdin;
\.


--
-- Name: oauth2_provider_accesstoken_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('oauth2_provider_accesstoken_id_seq', 1, false);


--
-- Data for Name: oauth2_provider_application; Type: TABLE DATA; Schema: public; Owner: -
--

COPY oauth2_provider_application (id, client_id, redirect_uris, client_type, authorization_grant_type, client_secret, name, user_id, skip_authorization) FROM stdin;
\.


--
-- Name: oauth2_provider_application_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('oauth2_provider_application_id_seq', 1, false);


--
-- Data for Name: oauth2_provider_grant; Type: TABLE DATA; Schema: public; Owner: -
--

COPY oauth2_provider_grant (id, code, expires, redirect_uri, scope, application_id, user_id) FROM stdin;
\.


--
-- Name: oauth2_provider_grant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('oauth2_provider_grant_id_seq', 1, false);


--
-- Data for Name: oauth2_provider_refreshtoken; Type: TABLE DATA; Schema: public; Owner: -
--

COPY oauth2_provider_refreshtoken (id, token, access_token_id, application_id, user_id) FROM stdin;
\.


--
-- Name: oauth2_provider_refreshtoken_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('oauth2_provider_refreshtoken_id_seq', 1, false);


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

COPY reports_budgetdailystatement (id, date, media_spend_nano, data_spend_nano, license_fee_nano, budget_id, margin_nano) FROM stdin;
\.


--
-- Name: reports_budgetdailystatement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_budgetdailystatement_id_seq', 1, false);


--
-- Data for Name: reports_budgetdailystatementk1; Type: TABLE DATA; Schema: public; Owner: -
--

COPY reports_budgetdailystatementk1 (id, date, media_spend_nano, data_spend_nano, license_fee_nano, budget_id) FROM stdin;
\.


--
-- Name: reports_budgetdailystatementk1_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_budgetdailystatementk1_id_seq', 1, false);


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

COPY reports_supplyreportrecipient (id, first_name, last_name, email, created_dt, modified_dt, source_id, publishers_report) FROM stdin;
\.


--
-- Name: reports_supplyreportrecipient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('reports_supplyreportrecipient_id_seq', 1, false);


--
-- Data for Name: restapi_reportjob; Type: TABLE DATA; Schema: public; Owner: -
--

COPY restapi_reportjob (id, created_dt, status, query, result, user_id) FROM stdin;
\.


--
-- Name: restapi_reportjob_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('restapi_reportjob_id_seq', 1, false);


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

COPY zemauth_user (id, password, last_login, is_superuser, email, username, first_name, last_name, date_joined, is_staff, is_active, is_test_user) FROM stdin;
1	pbkdf2_sha256$24000$GSWijssN2W0b$J0Hd1hjyMLM6BIn9xKPDSRlNU8IYx8QvqkcQPo+PI8Y=	2016-09-16 13:18:05.637437+00	t	dev@zemanta.com	\N			2016-09-16 13:18:05.637437+00	t	t	f
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
-- Name: actionlog_actionlog actionlog_actionlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_actionlog_pkey PRIMARY KEY (id);


--
-- Name: actionlog_actionlogorder actionlog_actionlogorder_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlogorder
    ADD CONSTRAINT actionlog_actionlogorder_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog automation_autopilotadgroupsourcebidcpclog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_autopilotadgroupsourcebidcpclog_pkey PRIMARY KEY (id);


--
-- Name: automation_autopilotlog automation_autopilotlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog
    ADD CONSTRAINT automation_autopilotlog_pkey PRIMARY KEY (id);


--
-- Name: automation_campaignbudgetdepletionnotification automation_campaignbudgetdepletionnotification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_campaignbudgetdepletionnotification_pkey PRIMARY KEY (id);


--
-- Name: automation_campaignstoplog automation_campaignstoplog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignstoplog
    ADD CONSTRAINT automation_campaignstoplog_pkey PRIMARY KEY (id);


--
-- Name: bizwire_adgrouptargeting bizwire_adgrouptargeting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY bizwire_adgrouptargeting
    ADD CONSTRAINT bizwire_adgrouptargeting_pkey PRIMARY KEY (id);


--
-- Name: bizwire_adgrouptargeting bizwire_adgrouptargeting_start_date_5b20e475_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY bizwire_adgrouptargeting
    ADD CONSTRAINT bizwire_adgrouptargeting_start_date_5b20e475_uniq UNIQUE (start_date, interest_targeting);


--
-- Name: dash_account_allowed_sources dash_account_allowed_sources_account_id_50157193_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allowed_sources_account_id_50157193_uniq UNIQUE (account_id, source_id);


--
-- Name: dash_account_allowed_sources dash_account_allowed_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allowed_sources_pkey PRIMARY KEY (id);


--
-- Name: dash_account_groups dash_account_groups_account_id_ba4a2f3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_account_id_ba4a2f3b_uniq UNIQUE (account_id, group_id);


--
-- Name: dash_account_groups dash_account_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_pkey PRIMARY KEY (id);


--
-- Name: dash_account dash_account_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_name_key UNIQUE (name);


--
-- Name: dash_account dash_account_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_pkey PRIMARY KEY (id);


--
-- Name: dash_account_users dash_account_users_account_id_3bba0949_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_account_id_3bba0949_uniq UNIQUE (account_id, user_id);


--
-- Name: dash_account_users dash_account_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_pkey PRIMARY KEY (id);


--
-- Name: dash_accountsettings dash_accountsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroup dash_adgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsettings dash_adgroupsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsource dash_adgroupsource_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsourcesettings dash_adgroupsourcesettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgroupsourcesettings_pkey PRIMARY KEY (id);


--
-- Name: dash_adgroupsourcestate dash_adgroupsourcestate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcestate
    ADD CONSTRAINT dash_adgroupsourcestate_pkey PRIMARY KEY (id);


--
-- Name: dash_agency dash_agency_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency
    ADD CONSTRAINT dash_agency_name_key UNIQUE (name);


--
-- Name: dash_agency dash_agency_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency
    ADD CONSTRAINT dash_agency_pkey PRIMARY KEY (id);


--
-- Name: dash_agency_users dash_agency_users_agency_id_a3210548_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency_users
    ADD CONSTRAINT dash_agency_users_agency_id_a3210548_uniq UNIQUE (agency_id, user_id);


--
-- Name: dash_agency_users dash_agency_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency_users
    ADD CONSTRAINT dash_agency_users_pkey PRIMARY KEY (id);


--
-- Name: dash_article dash_article_ad_group_id_1760d75c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_ad_group_id_1760d75c_uniq UNIQUE (ad_group_id, url, title);


--
-- Name: dash_article dash_article_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_pkey PRIMARY KEY (id);


--
-- Name: dash_audience dash_audience_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audience
    ADD CONSTRAINT dash_audience_pkey PRIMARY KEY (id);


--
-- Name: dash_budgethistory dash_budgethistory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethistory_pkey PRIMARY KEY (id);


--
-- Name: dash_budgetlineitem dash_budgetlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlineitem_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_groups dash_campaign_groups_campaign_id_3c58b972_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_campaign_id_3c58b972_uniq UNIQUE (campaign_id, group_id);


--
-- Name: dash_campaign_groups dash_campaign_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign dash_campaign_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_pkey PRIMARY KEY (id);


--
-- Name: dash_campaign_users dash_campaign_users_campaign_id_38d055a7_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_campaign_id_38d055a7_uniq UNIQUE (campaign_id, user_id);


--
-- Name: dash_campaign_users dash_campaign_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_pkey PRIMARY KEY (id);


--
-- Name: dash_campaigngoal dash_campaigngoal_campaign_id_c8136e9c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigngoal_campaign_id_c8136e9c_uniq UNIQUE (campaign_id, type, conversion_goal_id);


--
-- Name: dash_campaigngoal dash_campaigngoal_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigngoal_pkey PRIMARY KEY (id);


--
-- Name: dash_campaigngoalvalue dash_campaigngoalvalue_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue
    ADD CONSTRAINT dash_campaigngoalvalue_pkey PRIMARY KEY (id);


--
-- Name: dash_campaignsettings dash_campaignsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaignsettings_pkey PRIMARY KEY (id);


--
-- Name: dash_contentad dash_contentad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_pkey PRIMARY KEY (id);


--
-- Name: dash_contentadcandidate dash_contentadcandidate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadcandidate
    ADD CONSTRAINT dash_contentadcandidate_pkey PRIMARY KEY (id);


--
-- Name: dash_contentadsource dash_contentadsource_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsource_pkey PRIMARY KEY (id);


--
-- Name: dash_conversiongoal dash_conversiongoal_campaign_id_b9186b3c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_b9186b3c_uniq UNIQUE (campaign_id, name);


--
-- Name: dash_conversiongoal dash_conversiongoal_campaign_id_e9122092_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_e9122092_uniq UNIQUE (campaign_id, type, goal_id);


--
-- Name: dash_conversiongoal dash_conversiongoal_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_pkey PRIMARY KEY (id);


--
-- Name: dash_conversionpixel dash_conversionpixel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_pkey PRIMARY KEY (id);


--
-- Name: dash_conversionpixel dash_conversionpixel_slug_4e6ddb24_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_slug_4e6ddb24_uniq UNIQUE (slug, account_id);


--
-- Name: dash_credithistory dash_credithistory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithistory_pkey PRIMARY KEY (id);


--
-- Name: dash_creditlineitem dash_creditlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlineitem_pkey PRIMARY KEY (id);


--
-- Name: dash_defaultsourcesettings dash_defaultsourcesettings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_pkey PRIMARY KEY (id);


--
-- Name: dash_defaultsourcesettings dash_defaultsourcesettings_source_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_source_id_key UNIQUE (source_id);


--
-- Name: dash_demomapping dash_demomapping_demo_account_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demomapping
    ADD CONSTRAINT dash_demomapping_demo_account_name_key UNIQUE (demo_account_name);


--
-- Name: dash_demomapping dash_demomapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demomapping
    ADD CONSTRAINT dash_demomapping_pkey PRIMARY KEY (id);


--
-- Name: dash_demomapping dash_demomapping_real_account_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demomapping
    ADD CONSTRAINT dash_demomapping_real_account_id_key UNIQUE (real_account_id);


--
-- Name: dash_emailtemplate dash_emailtemplate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_emailtemplate
    ADD CONSTRAINT dash_emailtemplate_pkey PRIMARY KEY (id);


--
-- Name: dash_emailtemplate dash_emailtemplate_template_type_d3c24b36_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_emailtemplate
    ADD CONSTRAINT dash_emailtemplate_template_type_d3c24b36_uniq UNIQUE (template_type);


--
-- Name: dash_exportreport_filtered_agencies dash_exportreport_filtered_agenci_exportreport_id_3c20ad32_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_agencies
    ADD CONSTRAINT dash_exportreport_filtered_agenci_exportreport_id_3c20ad32_uniq UNIQUE (exportreport_id, agency_id);


--
-- Name: dash_exportreport_filtered_agencies dash_exportreport_filtered_agencies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_agencies
    ADD CONSTRAINT dash_exportreport_filtered_agencies_pkey PRIMARY KEY (id);


--
-- Name: dash_exportreport_filtered_sources dash_exportreport_filtered_source_exportreport_id_a5a44139_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_source_exportreport_id_a5a44139_uniq UNIQUE (exportreport_id, source_id);


--
-- Name: dash_exportreport_filtered_sources dash_exportreport_filtered_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_sources_pkey PRIMARY KEY (id);


--
-- Name: dash_exportreport dash_exportreport_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_pkey PRIMARY KEY (id);


--
-- Name: dash_facebookaccount dash_facebookaccount_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_facebookaccount
    ADD CONSTRAINT dash_facebookaccount_pkey PRIMARY KEY (account_id);


--
-- Name: dash_history dash_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history
    ADD CONSTRAINT dash_history_pkey PRIMARY KEY (id);


--
-- Name: dash_outbrainaccount dash_outbrainaccount_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_outbrainaccount
    ADD CONSTRAINT dash_outbrainaccount_pkey PRIMARY KEY (id);


--
-- Name: dash_publisherblacklist dash_publisherblacklist_name_daca9efc_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_name_daca9efc_uniq UNIQUE (name, everywhere, account_id, campaign_id, ad_group_id, source_id);


--
-- Name: dash_publisherblacklist dash_publisherblacklist_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_pkey PRIMARY KEY (id);


--
-- Name: dash_audiencerule dash_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audiencerule
    ADD CONSTRAINT dash_rule_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportreport dash_scheduledexportreport_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_scheduledexportreport_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportreportlog dash_scheduledexportreportlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportlog
    ADD CONSTRAINT dash_scheduledexportreportlog_pkey PRIMARY KEY (id);


--
-- Name: dash_scheduledexportreportrecipient dash_scheduledexportreportrec_scheduled_report_id_8c7e470d_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT dash_scheduledexportreportrec_scheduled_report_id_8c7e470d_uniq UNIQUE (scheduled_report_id, email);


--
-- Name: dash_scheduledexportreportrecipient dash_scheduledexportreportrecipient_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT dash_scheduledexportreportrecipient_pkey PRIMARY KEY (id);


--
-- Name: dash_source dash_source_bidder_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_bidder_slug_key UNIQUE (bidder_slug);


--
-- Name: dash_source dash_source_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_pkey PRIMARY KEY (id);


--
-- Name: dash_source dash_source_tracking_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_tracking_slug_key UNIQUE (tracking_slug);


--
-- Name: dash_sourcecredentials dash_sourcecredentials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcecredentials
    ADD CONSTRAINT dash_sourcecredentials_pkey PRIMARY KEY (id);


--
-- Name: dash_sourcetype dash_sourcetype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetype
    ADD CONSTRAINT dash_sourcetype_pkey PRIMARY KEY (id);


--
-- Name: dash_sourcetype dash_sourcetype_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetype
    ADD CONSTRAINT dash_sourcetype_type_key UNIQUE (type);


--
-- Name: dash_sourcetypepixel dash_sourcetypepixel_pixel_id_722518f4_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetypepixel
    ADD CONSTRAINT dash_sourcetypepixel_pixel_id_722518f4_uniq UNIQUE (pixel_id, source_type_id);


--
-- Name: dash_sourcetypepixel dash_sourcetypepixel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetypepixel
    ADD CONSTRAINT dash_sourcetypepixel_pkey PRIMARY KEY (id);


--
-- Name: dash_uploadbatch dash_uploadbatch_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_uploadbatch
    ADD CONSTRAINT dash_uploadbatch_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: oauth2_provider_accesstoken oauth2_provider_accesstoken_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_accesstoken
    ADD CONSTRAINT oauth2_provider_accesstoken_pkey PRIMARY KEY (id);


--
-- Name: oauth2_provider_application oauth2_provider_application_client_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_application
    ADD CONSTRAINT oauth2_provider_application_client_id_key UNIQUE (client_id);


--
-- Name: oauth2_provider_application oauth2_provider_application_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_application
    ADD CONSTRAINT oauth2_provider_application_pkey PRIMARY KEY (id);


--
-- Name: oauth2_provider_grant oauth2_provider_grant_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_grant
    ADD CONSTRAINT oauth2_provider_grant_pkey PRIMARY KEY (id);


--
-- Name: oauth2_provider_refreshtoken oauth2_provider_refreshtoken_access_token_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_refreshtoken
    ADD CONSTRAINT oauth2_provider_refreshtoken_access_token_id_key UNIQUE (access_token_id);


--
-- Name: oauth2_provider_refreshtoken oauth2_provider_refreshtoken_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_refreshtoken
    ADD CONSTRAINT oauth2_provider_refreshtoken_pkey PRIMARY KEY (id);


--
-- Name: reports_adgroupgoalconversionstats reports_adgroupgoalconversionstats_datetime_e7d98b86_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconversionstats_datetime_e7d98b86_uniq UNIQUE (datetime, ad_group_id, source_id, goal_name);


--
-- Name: reports_adgroupgoalconversionstats reports_adgroupgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_adgroupstats reports_adgroupstats_datetime_991f66e4_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_datetime_991f66e4_uniq UNIQUE (datetime, ad_group_id, source_id);


--
-- Name: reports_adgroupstats reports_adgroupstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_pkey PRIMARY KEY (id);


--
-- Name: reports_articlestats reports_articlestats_datetime_0feb402c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_datetime_0feb402c_uniq UNIQUE (datetime, ad_group_id, article_id, source_id);


--
-- Name: reports_articlestats reports_articlestats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_pkey PRIMARY KEY (id);


--
-- Name: reports_budgetdailystatement reports_budgetdailystatement_budget_id_89c57151_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatement
    ADD CONSTRAINT reports_budgetdailystatement_budget_id_89c57151_uniq UNIQUE (budget_id, date);


--
-- Name: reports_budgetdailystatement reports_budgetdailystatement_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatement
    ADD CONSTRAINT reports_budgetdailystatement_pkey PRIMARY KEY (id);


--
-- Name: reports_budgetdailystatementk1 reports_budgetdailystatementk1_budget_id_a0bbce8f_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatementk1
    ADD CONSTRAINT reports_budgetdailystatementk1_budget_id_a0bbce8f_uniq UNIQUE (budget_id, date);


--
-- Name: reports_budgetdailystatementk1 reports_budgetdailystatementk1_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatementk1
    ADD CONSTRAINT reports_budgetdailystatementk1_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadgoalconversionstats reports_contentadgoalconversionstats_date_40bd10c6_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconversionstats_date_40bd10c6_uniq UNIQUE (date, content_ad_id, source_id, goal_type, goal_name);


--
-- Name: reports_contentadgoalconversionstats reports_contentadgoalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadpostclickstats reports_contentadpostclickstats_date_3d726b82_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclickstats_date_3d726b82_uniq UNIQUE (date, content_ad_id, source_id);


--
-- Name: reports_contentadpostclickstats reports_contentadpostclickstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclickstats_pkey PRIMARY KEY (id);


--
-- Name: reports_contentadstats reports_contentadstats_date_ff0cbc01_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_date_ff0cbc01_uniq UNIQUE (date, content_ad_source_id);


--
-- Name: reports_contentadstats reports_contentadstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_pkey PRIMARY KEY (id);


--
-- Name: reports_goalconversionstats reports_goalconversionstats_datetime_59bc9db3_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstats_datetime_59bc9db3_uniq UNIQUE (datetime, ad_group_id, article_id, source_id, goal_name);


--
-- Name: reports_goalconversionstats reports_goalconversionstats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstats_pkey PRIMARY KEY (id);


--
-- Name: reports_supplyreportrecipient reports_supplyreportrecipient_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyreportrecipient_pkey PRIMARY KEY (id);


--
-- Name: restapi_reportjob restapi_reportjob_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY restapi_reportjob
    ADD CONSTRAINT restapi_reportjob_pkey PRIMARY KEY (id);


--
-- Name: zemauth_internalgroup zemauth_internalgroup_group_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_group_id_key UNIQUE (group_id);


--
-- Name: zemauth_internalgroup zemauth_internalgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user zemauth_user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user
    ADD CONSTRAINT zemauth_user_email_key UNIQUE (email);


--
-- Name: zemauth_user_groups zemauth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_groups zemauth_user_groups_user_id_4227bf89_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_user_id_4227bf89_uniq UNIQUE (user_id, group_id);


--
-- Name: zemauth_user zemauth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user
    ADD CONSTRAINT zemauth_user_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_user_permissions zemauth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: zemauth_user_user_permissions zemauth_user_user_permissions_user_id_507a77eb_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissions_user_id_507a77eb_uniq UNIQUE (user_id, permission_id);


--
-- Name: actionlog_actionlog_0b893638; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_0b893638 ON actionlog_actionlog USING btree (created_dt);


--
-- Name: actionlog_actionlog_418c5509; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_418c5509 ON actionlog_actionlog USING btree (action);


--
-- Name: actionlog_actionlog_69dfcb07; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_69dfcb07 ON actionlog_actionlog USING btree (order_id);


--
-- Name: actionlog_actionlog_87f78d4d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_87f78d4d ON actionlog_actionlog USING btree (content_ad_source_id);


--
-- Name: actionlog_actionlog_9ed39e2e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_9ed39e2e ON actionlog_actionlog USING btree (state);


--
-- Name: actionlog_actionlog_a8060d34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_a8060d34 ON actionlog_actionlog USING btree (ad_group_source_id);


--
-- Name: actionlog_actionlog_action_884cdc95_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_action_884cdc95_like ON actionlog_actionlog USING btree (action varchar_pattern_ops);


--
-- Name: actionlog_actionlog_b3da0983; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_b3da0983 ON actionlog_actionlog USING btree (modified_by_id);


--
-- Name: actionlog_actionlog_c3fc31da; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_c3fc31da ON actionlog_actionlog USING btree (modified_dt);


--
-- Name: actionlog_actionlog_ca47336a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_ca47336a ON actionlog_actionlog USING btree (action_type);


--
-- Name: actionlog_actionlog_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_e93cb7eb ON actionlog_actionlog USING btree (created_by_id);


--
-- Name: actionlog_actionlog_id_d0bab7a7_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actionlog_actionlog_id_d0bab7a7_idx ON actionlog_actionlog USING btree (id, created_dt);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_name_a6ea08ec_like ON auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_0e939a4f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_0e939a4f ON auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_8373b171; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_8373b171 ON auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_417f1b1c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_permission_417f1b1c ON auth_permission USING btree (content_type_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_0b893638; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_0b893638 ON automation_autopilotadgroupsourcebidcpclog USING btree (created_dt);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_22ff94c4 ON automation_autopilotadgroupsourcebidcpclog USING btree (ad_group_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_a8060d34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_a8060d34 ON automation_autopilotadgroupsourcebidcpclog USING btree (ad_group_source_id);


--
-- Name: automation_autopilotadgroupsourcebidcpclog_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotadgroupsourcebidcpclog_f14acec3 ON automation_autopilotadgroupsourcebidcpclog USING btree (campaign_id);


--
-- Name: automation_autopilotlog_0b893638; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotlog_0b893638 ON automation_autopilotlog USING btree (created_dt);


--
-- Name: automation_autopilotlog_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotlog_22ff94c4 ON automation_autopilotlog USING btree (ad_group_id);


--
-- Name: automation_autopilotlog_a8060d34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_autopilotlog_a8060d34 ON automation_autopilotlog USING btree (ad_group_source_id);


--
-- Name: automation_campaignbudgetdepletionnotification_0b893638; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_campaignbudgetdepletionnotification_0b893638 ON automation_campaignbudgetdepletionnotification USING btree (created_dt);


--
-- Name: automation_campaignbudgetdepletionnotification_6bc80cbd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_campaignbudgetdepletionnotification_6bc80cbd ON automation_campaignbudgetdepletionnotification USING btree (account_manager_id);


--
-- Name: automation_campaignbudgetdepletionnotification_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_campaignbudgetdepletionnotification_f14acec3 ON automation_campaignbudgetdepletionnotification USING btree (campaign_id);


--
-- Name: automation_campaignstoplog_0b893638; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_campaignstoplog_0b893638 ON automation_campaignstoplog USING btree (created_dt);


--
-- Name: automation_campaignstoplog_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX automation_campaignstoplog_f14acec3 ON automation_campaignstoplog USING btree (campaign_id);


--
-- Name: bizwire_adgrouptargeting_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX bizwire_adgrouptargeting_22ff94c4 ON bizwire_adgrouptargeting USING btree (ad_group_id);


--
-- Name: dash_account_169fc544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_169fc544 ON dash_account USING btree (agency_id);


--
-- Name: dash_account_allowed_sources_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_allowed_sources_0afd9202 ON dash_account_allowed_sources USING btree (source_id);


--
-- Name: dash_account_allowed_sources_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_allowed_sources_8a089c2a ON dash_account_allowed_sources USING btree (account_id);


--
-- Name: dash_account_b3da0983; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_b3da0983 ON dash_account USING btree (modified_by_id);


--
-- Name: dash_account_groups_0e939a4f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_groups_0e939a4f ON dash_account_groups USING btree (group_id);


--
-- Name: dash_account_groups_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_groups_8a089c2a ON dash_account_groups USING btree (account_id);


--
-- Name: dash_account_name_b55f3cd6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_name_b55f3cd6_like ON dash_account USING btree (name varchar_pattern_ops);


--
-- Name: dash_account_users_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_users_8a089c2a ON dash_account_users USING btree (account_id);


--
-- Name: dash_account_users_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_account_users_e8701ad4 ON dash_account_users USING btree (user_id);


--
-- Name: dash_accountsettings_49e3f602; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_accountsettings_49e3f602 ON dash_accountsettings USING btree (default_account_manager_id);


--
-- Name: dash_accountsettings_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_accountsettings_8a089c2a ON dash_accountsettings USING btree (account_id);


--
-- Name: dash_accountsettings_b6c58ed1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_accountsettings_b6c58ed1 ON dash_accountsettings USING btree (default_sales_representative_id);


--
-- Name: dash_accountsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_accountsettings_e93cb7eb ON dash_accountsettings USING btree (created_by_id);


--
-- Name: dash_adgroup_b3da0983; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroup_b3da0983 ON dash_adgroup USING btree (modified_by_id);


--
-- Name: dash_adgroup_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroup_f14acec3 ON dash_adgroup USING btree (campaign_id);


--
-- Name: dash_adgroupsettings_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsettings_22ff94c4 ON dash_adgroupsettings USING btree (ad_group_id);


--
-- Name: dash_adgroupsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsettings_e93cb7eb ON dash_adgroupsettings USING btree (created_by_id);


--
-- Name: dash_adgroupsource_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsource_0afd9202 ON dash_adgroupsource USING btree (source_id);


--
-- Name: dash_adgroupsource_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsource_22ff94c4 ON dash_adgroupsource USING btree (ad_group_id);


--
-- Name: dash_adgroupsource_709deb08; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsource_709deb08 ON dash_adgroupsource USING btree (source_credentials_id);


--
-- Name: dash_adgroupsourcesettings_a8060d34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsourcesettings_a8060d34 ON dash_adgroupsourcesettings USING btree (ad_group_source_id);


--
-- Name: dash_adgroupsourcesettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsourcesettings_e93cb7eb ON dash_adgroupsourcesettings USING btree (created_by_id);


--
-- Name: dash_adgroupsourcestate_a8060d34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_adgroupsourcestate_a8060d34 ON dash_adgroupsourcestate USING btree (ad_group_source_id);


--
-- Name: dash_agency_3ddf5938; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_agency_3ddf5938 ON dash_agency USING btree (sales_representative_id);


--
-- Name: dash_agency_b3da0983; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_agency_b3da0983 ON dash_agency USING btree (modified_by_id);


--
-- Name: dash_agency_name_f023415b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_agency_name_f023415b_like ON dash_agency USING btree (name varchar_pattern_ops);


--
-- Name: dash_agency_users_169fc544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_agency_users_169fc544 ON dash_agency_users USING btree (agency_id);


--
-- Name: dash_agency_users_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_agency_users_e8701ad4 ON dash_agency_users USING btree (user_id);


--
-- Name: dash_article_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_article_22ff94c4 ON dash_article USING btree (ad_group_id);


--
-- Name: dash_audience_ba2eed6c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_audience_ba2eed6c ON dash_audience USING btree (pixel_id);


--
-- Name: dash_audience_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_audience_e93cb7eb ON dash_audience USING btree (created_by_id);


--
-- Name: dash_budgethistory_7748a592; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_budgethistory_7748a592 ON dash_budgethistory USING btree (budget_id);


--
-- Name: dash_budgethistory_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_budgethistory_e93cb7eb ON dash_budgethistory USING btree (created_by_id);


--
-- Name: dash_budgetlineitem_5097e6b2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_budgetlineitem_5097e6b2 ON dash_budgetlineitem USING btree (credit_id);


--
-- Name: dash_budgetlineitem_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_budgetlineitem_e93cb7eb ON dash_budgetlineitem USING btree (created_by_id);


--
-- Name: dash_budgetlineitem_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_budgetlineitem_f14acec3 ON dash_budgetlineitem USING btree (campaign_id);


--
-- Name: dash_campaign_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaign_8a089c2a ON dash_campaign USING btree (account_id);


--
-- Name: dash_campaign_b3da0983; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaign_b3da0983 ON dash_campaign USING btree (modified_by_id);


--
-- Name: dash_campaign_groups_0e939a4f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaign_groups_0e939a4f ON dash_campaign_groups USING btree (group_id);


--
-- Name: dash_campaign_groups_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaign_groups_f14acec3 ON dash_campaign_groups USING btree (campaign_id);


--
-- Name: dash_campaign_users_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaign_users_e8701ad4 ON dash_campaign_users USING btree (user_id);


--
-- Name: dash_campaign_users_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaign_users_f14acec3 ON dash_campaign_users USING btree (campaign_id);


--
-- Name: dash_campaigngoal_b216c85c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaigngoal_b216c85c ON dash_campaigngoal USING btree (conversion_goal_id);


--
-- Name: dash_campaigngoal_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaigngoal_e93cb7eb ON dash_campaigngoal USING btree (created_by_id);


--
-- Name: dash_campaigngoal_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaigngoal_f14acec3 ON dash_campaigngoal USING btree (campaign_id);


--
-- Name: dash_campaigngoalvalue_80fa406a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaigngoalvalue_80fa406a ON dash_campaigngoalvalue USING btree (campaign_goal_id);


--
-- Name: dash_campaigngoalvalue_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaigngoalvalue_e93cb7eb ON dash_campaigngoalvalue USING btree (created_by_id);


--
-- Name: dash_campaignsettings_548b53b3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaignsettings_548b53b3 ON dash_campaignsettings USING btree (iab_category);


--
-- Name: dash_campaignsettings_dd7656fc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaignsettings_dd7656fc ON dash_campaignsettings USING btree (campaign_manager_id);


--
-- Name: dash_campaignsettings_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaignsettings_e93cb7eb ON dash_campaignsettings USING btree (created_by_id);


--
-- Name: dash_campaignsettings_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaignsettings_f14acec3 ON dash_campaignsettings USING btree (campaign_id);


--
-- Name: dash_campaignsettings_iab_category_2cabefa1_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_campaignsettings_iab_category_2cabefa1_like ON dash_campaignsettings USING btree (iab_category varchar_pattern_ops);


--
-- Name: dash_contentad_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_contentad_22ff94c4 ON dash_contentad USING btree (ad_group_id);


--
-- Name: dash_contentad_d4e60137; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_contentad_d4e60137 ON dash_contentad USING btree (batch_id);


--
-- Name: dash_contentadcandidate_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_contentadcandidate_22ff94c4 ON dash_contentadcandidate USING btree (ad_group_id);


--
-- Name: dash_contentadcandidate_d4e60137; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_contentadcandidate_d4e60137 ON dash_contentadcandidate USING btree (batch_id);


--
-- Name: dash_contentadsource_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_contentadsource_0afd9202 ON dash_contentadsource USING btree (source_id);


--
-- Name: dash_contentadsource_abf89b3f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_contentadsource_abf89b3f ON dash_contentadsource USING btree (content_ad_id);


--
-- Name: dash_conversiongoal_ba2eed6c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_conversiongoal_ba2eed6c ON dash_conversiongoal USING btree (pixel_id);


--
-- Name: dash_conversiongoal_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_conversiongoal_f14acec3 ON dash_conversiongoal USING btree (campaign_id);


--
-- Name: dash_conversionpixel_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_conversionpixel_8a089c2a ON dash_conversionpixel USING btree (account_id);


--
-- Name: dash_credithistory_5097e6b2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_credithistory_5097e6b2 ON dash_credithistory USING btree (credit_id);


--
-- Name: dash_credithistory_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_credithistory_e93cb7eb ON dash_credithistory USING btree (created_by_id);


--
-- Name: dash_creditlineitem_169fc544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_creditlineitem_169fc544 ON dash_creditlineitem USING btree (agency_id);


--
-- Name: dash_creditlineitem_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_creditlineitem_8a089c2a ON dash_creditlineitem USING btree (account_id);


--
-- Name: dash_creditlineitem_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_creditlineitem_e93cb7eb ON dash_creditlineitem USING btree (created_by_id);


--
-- Name: dash_defaultsourcesettings_9d2c2cd1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_defaultsourcesettings_9d2c2cd1 ON dash_defaultsourcesettings USING btree (credentials_id);


--
-- Name: dash_demomapping_demo_account_name_a91e36fa_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_demomapping_demo_account_name_a91e36fa_like ON dash_demomapping USING btree (demo_account_name varchar_pattern_ops);


--
-- Name: dash_exportreport_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_22ff94c4 ON dash_exportreport USING btree (ad_group_id);


--
-- Name: dash_exportreport_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_8a089c2a ON dash_exportreport USING btree (account_id);


--
-- Name: dash_exportreport_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_e93cb7eb ON dash_exportreport USING btree (created_by_id);


--
-- Name: dash_exportreport_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_f14acec3 ON dash_exportreport USING btree (campaign_id);


--
-- Name: dash_exportreport_filtered_agencies_169fc544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_filtered_agencies_169fc544 ON dash_exportreport_filtered_agencies USING btree (agency_id);


--
-- Name: dash_exportreport_filtered_agencies_aa7beb1a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_filtered_agencies_aa7beb1a ON dash_exportreport_filtered_agencies USING btree (exportreport_id);


--
-- Name: dash_exportreport_filtered_sources_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_filtered_sources_0afd9202 ON dash_exportreport_filtered_sources USING btree (source_id);


--
-- Name: dash_exportreport_filtered_sources_aa7beb1a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_exportreport_filtered_sources_aa7beb1a ON dash_exportreport_filtered_sources USING btree (exportreport_id);


--
-- Name: dash_history_169fc544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_history_169fc544 ON dash_history USING btree (agency_id);


--
-- Name: dash_history_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_history_22ff94c4 ON dash_history USING btree (ad_group_id);


--
-- Name: dash_history_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_history_8a089c2a ON dash_history USING btree (account_id);


--
-- Name: dash_history_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_history_e93cb7eb ON dash_history USING btree (created_by_id);


--
-- Name: dash_history_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_history_f14acec3 ON dash_history USING btree (campaign_id);


--
-- Name: dash_publisherblacklist_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_publisherblacklist_0afd9202 ON dash_publisherblacklist USING btree (source_id);


--
-- Name: dash_publisherblacklist_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_publisherblacklist_22ff94c4 ON dash_publisherblacklist USING btree (ad_group_id);


--
-- Name: dash_publisherblacklist_8a089c2a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_publisherblacklist_8a089c2a ON dash_publisherblacklist USING btree (account_id);


--
-- Name: dash_publisherblacklist_f14acec3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_publisherblacklist_f14acec3 ON dash_publisherblacklist USING btree (campaign_id);


--
-- Name: dash_rule_cc4f3858; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_rule_cc4f3858 ON dash_audiencerule USING btree (audience_id);


--
-- Name: dash_scheduledexportreport_6f78b20c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_scheduledexportreport_6f78b20c ON dash_scheduledexportreport USING btree (report_id);


--
-- Name: dash_scheduledexportreport_e93cb7eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_scheduledexportreport_e93cb7eb ON dash_scheduledexportreport USING btree (created_by_id);


--
-- Name: dash_scheduledexportreportlog_4deefed9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_scheduledexportreportlog_4deefed9 ON dash_scheduledexportreportlog USING btree (scheduled_report_id);


--
-- Name: dash_scheduledexportreportrecipient_4deefed9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_scheduledexportreportrecipient_4deefed9 ON dash_scheduledexportreportrecipient USING btree (scheduled_report_id);


--
-- Name: dash_source_bidder_slug_e16a30eb_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_source_bidder_slug_e16a30eb_like ON dash_source USING btree (bidder_slug varchar_pattern_ops);


--
-- Name: dash_source_ed5cb66b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_source_ed5cb66b ON dash_source USING btree (source_type_id);


--
-- Name: dash_source_tracking_slug_158490d2_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_source_tracking_slug_158490d2_like ON dash_source USING btree (tracking_slug varchar_pattern_ops);


--
-- Name: dash_sourcecredentials_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_sourcecredentials_0afd9202 ON dash_sourcecredentials USING btree (source_id);


--
-- Name: dash_sourcetype_type_557e3620_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_sourcetype_type_557e3620_like ON dash_sourcetype USING btree (type varchar_pattern_ops);


--
-- Name: dash_sourcetypepixel_ba2eed6c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_sourcetypepixel_ba2eed6c ON dash_sourcetypepixel USING btree (pixel_id);


--
-- Name: dash_sourcetypepixel_ed5cb66b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_sourcetypepixel_ed5cb66b ON dash_sourcetypepixel USING btree (source_type_id);


--
-- Name: dash_uploadbatch_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dash_uploadbatch_22ff94c4 ON dash_uploadbatch USING btree (ad_group_id);


--
-- Name: django_admin_log_417f1b1c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_417f1b1c ON django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_e8701ad4 ON django_admin_log USING btree (user_id);


--
-- Name: django_session_de54fa62; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_de54fa62 ON django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_session_key_c0390e0f_like ON django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: oauth2_provider_accesstoken_6bc0a4eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_accesstoken_6bc0a4eb ON oauth2_provider_accesstoken USING btree (application_id);


--
-- Name: oauth2_provider_accesstoken_94a08da1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_accesstoken_94a08da1 ON oauth2_provider_accesstoken USING btree (token);


--
-- Name: oauth2_provider_accesstoken_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_accesstoken_e8701ad4 ON oauth2_provider_accesstoken USING btree (user_id);


--
-- Name: oauth2_provider_accesstoken_token_8af090f8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_accesstoken_token_8af090f8_like ON oauth2_provider_accesstoken USING btree (token varchar_pattern_ops);


--
-- Name: oauth2_provider_application_9d667c2b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_application_9d667c2b ON oauth2_provider_application USING btree (client_secret);


--
-- Name: oauth2_provider_application_client_id_03f0cc84_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_application_client_id_03f0cc84_like ON oauth2_provider_application USING btree (client_id varchar_pattern_ops);


--
-- Name: oauth2_provider_application_client_secret_53133678_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_application_client_secret_53133678_like ON oauth2_provider_application USING btree (client_secret varchar_pattern_ops);


--
-- Name: oauth2_provider_application_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_application_e8701ad4 ON oauth2_provider_application USING btree (user_id);


--
-- Name: oauth2_provider_grant_6bc0a4eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_grant_6bc0a4eb ON oauth2_provider_grant USING btree (application_id);


--
-- Name: oauth2_provider_grant_c1336794; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_grant_c1336794 ON oauth2_provider_grant USING btree (code);


--
-- Name: oauth2_provider_grant_code_49ab4ddf_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_grant_code_49ab4ddf_like ON oauth2_provider_grant USING btree (code varchar_pattern_ops);


--
-- Name: oauth2_provider_grant_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_grant_e8701ad4 ON oauth2_provider_grant USING btree (user_id);


--
-- Name: oauth2_provider_refreshtoken_6bc0a4eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_refreshtoken_6bc0a4eb ON oauth2_provider_refreshtoken USING btree (application_id);


--
-- Name: oauth2_provider_refreshtoken_94a08da1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_refreshtoken_94a08da1 ON oauth2_provider_refreshtoken USING btree (token);


--
-- Name: oauth2_provider_refreshtoken_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_refreshtoken_e8701ad4 ON oauth2_provider_refreshtoken USING btree (user_id);


--
-- Name: oauth2_provider_refreshtoken_token_d090daa4_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX oauth2_provider_refreshtoken_token_d090daa4_like ON oauth2_provider_refreshtoken USING btree (token varchar_pattern_ops);


--
-- Name: reports_adgroupgoalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_adgroupgoalconversionstats_0afd9202 ON reports_adgroupgoalconversionstats USING btree (source_id);


--
-- Name: reports_adgroupgoalconversionstats_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_adgroupgoalconversionstats_22ff94c4 ON reports_adgroupgoalconversionstats USING btree (ad_group_id);


--
-- Name: reports_adgroupstats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_adgroupstats_0afd9202 ON reports_adgroupstats USING btree (source_id);


--
-- Name: reports_adgroupstats_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_adgroupstats_22ff94c4 ON reports_adgroupstats USING btree (ad_group_id);


--
-- Name: reports_articlestats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_articlestats_0afd9202 ON reports_articlestats USING btree (source_id);


--
-- Name: reports_articlestats_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_articlestats_22ff94c4 ON reports_articlestats USING btree (ad_group_id);


--
-- Name: reports_articlestats_a00c1b00; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_articlestats_a00c1b00 ON reports_articlestats USING btree (article_id);


--
-- Name: reports_articlestats_ad_group_id_b2526781_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_articlestats_ad_group_id_b2526781_idx ON reports_articlestats USING btree (ad_group_id, datetime);


--
-- Name: reports_budgetdailystatement_7748a592; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_budgetdailystatement_7748a592 ON reports_budgetdailystatement USING btree (budget_id);


--
-- Name: reports_budgetdailystatementk1_7748a592; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_budgetdailystatementk1_7748a592 ON reports_budgetdailystatementk1 USING btree (budget_id);


--
-- Name: reports_contentadgoalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadgoalconversionstats_0afd9202 ON reports_contentadgoalconversionstats USING btree (source_id);


--
-- Name: reports_contentadgoalconversionstats_197e2321; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadgoalconversionstats_197e2321 ON reports_contentadgoalconversionstats USING btree (goal_type);


--
-- Name: reports_contentadgoalconversionstats_abf89b3f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadgoalconversionstats_abf89b3f ON reports_contentadgoalconversionstats USING btree (content_ad_id);


--
-- Name: reports_contentadgoalconversionstats_goal_type_d582847b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadgoalconversionstats_goal_type_d582847b_like ON reports_contentadgoalconversionstats USING btree (goal_type varchar_pattern_ops);


--
-- Name: reports_contentadpostclickstats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadpostclickstats_0afd9202 ON reports_contentadpostclickstats USING btree (source_id);


--
-- Name: reports_contentadpostclickstats_abf89b3f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadpostclickstats_abf89b3f ON reports_contentadpostclickstats USING btree (content_ad_id);


--
-- Name: reports_contentadstats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadstats_0afd9202 ON reports_contentadstats USING btree (source_id);


--
-- Name: reports_contentadstats_87f78d4d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadstats_87f78d4d ON reports_contentadstats USING btree (content_ad_source_id);


--
-- Name: reports_contentadstats_abf89b3f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_contentadstats_abf89b3f ON reports_contentadstats USING btree (content_ad_id);


--
-- Name: reports_goalconversionstats_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_goalconversionstats_0afd9202 ON reports_goalconversionstats USING btree (source_id);


--
-- Name: reports_goalconversionstats_22ff94c4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_goalconversionstats_22ff94c4 ON reports_goalconversionstats USING btree (ad_group_id);


--
-- Name: reports_goalconversionstats_a00c1b00; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_goalconversionstats_a00c1b00 ON reports_goalconversionstats USING btree (article_id);


--
-- Name: reports_supplyreportrecipient_0afd9202; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reports_supplyreportrecipient_0afd9202 ON reports_supplyreportrecipient USING btree (source_id);


--
-- Name: restapi_reportjob_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX restapi_reportjob_e8701ad4 ON restapi_reportjob USING btree (user_id);


--
-- Name: zemauth_user_email_07ae32b7_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX zemauth_user_email_07ae32b7_like ON zemauth_user USING btree (email varchar_pattern_ops);


--
-- Name: zemauth_user_email_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user USING btree (lower((email)::text));


--
-- Name: zemauth_user_groups_0e939a4f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX zemauth_user_groups_0e939a4f ON zemauth_user_groups USING btree (group_id);


--
-- Name: zemauth_user_groups_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX zemauth_user_groups_e8701ad4 ON zemauth_user_groups USING btree (user_id);


--
-- Name: zemauth_user_user_permissions_8373b171; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX zemauth_user_user_permissions_8373b171 ON zemauth_user_user_permissions USING btree (permission_id);


--
-- Name: zemauth_user_user_permissions_e8701ad4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX zemauth_user_user_permissions_e8701ad4 ON zemauth_user_user_permissions USING btree (user_id);


--
-- Name: actionlog_actionlog action_content_ad_source_id_f725f3ed_fk_dash_contentadsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT action_content_ad_source_id_f725f3ed_fk_dash_contentadsource_id FOREIGN KEY (content_ad_source_id) REFERENCES dash_contentadsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_actionlog actionlog__ad_group_source_id_35a61de6_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog__ad_group_source_id_35a61de6_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_actionlog actionlog_acti_order_id_56ed85e1_fk_actionlog_actionlogorder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_acti_order_id_56ed85e1_fk_actionlog_actionlogorder_id FOREIGN KEY (order_id) REFERENCES actionlog_actionlogorder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_actionlog actionlog_actionlog_created_by_id_b0901110_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_actionlog_created_by_id_b0901110_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: actionlog_actionlog actionlog_actionlog_modified_by_id_54e9fd51_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY actionlog_actionlog
    ADD CONSTRAINT actionlog_actionlog_modified_by_id_54e9fd51_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permiss_permission_id_84c5c92e_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permiss_permission_id_84c5c92e_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permiss_content_type_id_2f476e4b_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permiss_content_type_id_2f476e4b_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_autopilotlog automation_ad_group_source_id_2c314f13_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog
    ADD CONSTRAINT automation_ad_group_source_id_2c314f13_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_autopilotadgroupsourcebidcpclog automation_ad_group_source_id_c4454460_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_ad_group_source_id_c4454460_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_autopilotadgroupsourcebidcpclog automation_autopilotad_campaign_id_dd13e45e_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_autopilotad_campaign_id_dd13e45e_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_autopilotadgroupsourcebidcpclog automation_autopilotadg_ad_group_id_4a5303df_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotadgroupsourcebidcpclog
    ADD CONSTRAINT automation_autopilotadg_ad_group_id_4a5303df_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_autopilotlog automation_autopilotlog_ad_group_id_bfdf0e7b_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_autopilotlog
    ADD CONSTRAINT automation_autopilotlog_ad_group_id_bfdf0e7b_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_campaignbudgetdepletionnotification automation_campa_account_manager_id_fac294a9_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_campa_account_manager_id_fac294a9_fk_zemauth_user_id FOREIGN KEY (account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_campaignbudgetdepletionnotification automation_campaignbud_campaign_id_3439ea40_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignbudgetdepletionnotification
    ADD CONSTRAINT automation_campaignbud_campaign_id_3439ea40_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: automation_campaignstoplog automation_campaignsto_campaign_id_c521c9c6_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY automation_campaignstoplog
    ADD CONSTRAINT automation_campaignsto_campaign_id_c521c9c6_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bizwire_adgrouptargeting bizwire_adgrouptargetin_ad_group_id_632c2fb8_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY bizwire_adgrouptargeting
    ADD CONSTRAINT bizwire_adgrouptargetin_ad_group_id_632c2fb8_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_scheduledexportreportlog d_scheduled_report_id_ab039ed6_fk_dash_scheduledexportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportlog
    ADD CONSTRAINT d_scheduled_report_id_ab039ed6_fk_dash_scheduledexportreport_id FOREIGN KEY (scheduled_report_id) REFERENCES dash_scheduledexportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_scheduledexportreportrecipient d_scheduled_report_id_fabfdb59_fk_dash_scheduledexportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreportrecipient
    ADD CONSTRAINT d_scheduled_report_id_fabfdb59_fk_dash_scheduledexportreport_id FOREIGN KEY (scheduled_report_id) REFERENCES dash_scheduledexportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountsettings das_default_sales_representative_id_def74ce7_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT das_default_sales_representative_id_def74ce7_fk_zemauth_user_id FOREIGN KEY (default_sales_representative_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsource das_source_credentials_id_5f1ac6cd_fk_dash_sourcecredentials_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT das_source_credentials_id_5f1ac6cd_fk_dash_sourcecredentials_id FOREIGN KEY (source_credentials_id) REFERENCES dash_sourcecredentials(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountsettings dash_acc_default_account_manager_id_b4b9d4c8_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_acc_default_account_manager_id_b4b9d4c8_fk_zemauth_user_id FOREIGN KEY (default_account_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account dash_account_agency_id_44ca3f6d_fk_dash_agency_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_agency_id_44ca3f6d_fk_dash_agency_id FOREIGN KEY (agency_id) REFERENCES dash_agency(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_allowed_sources dash_account_allowed_sou_account_id_e8009b9b_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allowed_sou_account_id_e8009b9b_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_allowed_sources dash_account_allowed_sourc_source_id_f18cfe92_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_allowed_sources
    ADD CONSTRAINT dash_account_allowed_sourc_source_id_f18cfe92_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_groups dash_account_groups_account_id_461f92b0_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_account_id_461f92b0_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_groups dash_account_groups_group_id_c840aed3_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_groups
    ADD CONSTRAINT dash_account_groups_group_id_c840aed3_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account dash_account_modified_by_id_e76cb440_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account
    ADD CONSTRAINT dash_account_modified_by_id_e76cb440_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_users dash_account_users_account_id_9edfb5fc_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_account_id_9edfb5fc_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_account_users dash_account_users_user_id_823aadd1_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_account_users
    ADD CONSTRAINT dash_account_users_user_id_823aadd1_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountsettings dash_accountsettings_account_id_32421162_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsettings_account_id_32421162_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_accountsettings dash_accountsettings_created_by_id_4abd7a29_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_accountsettings
    ADD CONSTRAINT dash_accountsettings_created_by_id_4abd7a29_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsourcestate dash_adgro_ad_group_source_id_077de87d_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcestate
    ADD CONSTRAINT dash_adgro_ad_group_source_id_077de87d_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsourcesettings dash_adgro_ad_group_source_id_204d5d32_fk_dash_adgroupsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgro_ad_group_source_id_204d5d32_fk_dash_adgroupsource_id FOREIGN KEY (ad_group_source_id) REFERENCES dash_adgroupsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroup dash_adgroup_campaign_id_f237eeaa_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_campaign_id_f237eeaa_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroup dash_adgroup_modified_by_id_ccdb9213_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroup
    ADD CONSTRAINT dash_adgroup_modified_by_id_ccdb9213_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsettings dash_adgroupsettings_ad_group_id_41cf8f77_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupsettings_ad_group_id_41cf8f77_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsettings dash_adgroupsettings_created_by_id_dcd2e743_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsettings
    ADD CONSTRAINT dash_adgroupsettings_created_by_id_dcd2e743_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsource dash_adgroupsource_ad_group_id_219ae0a9_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_ad_group_id_219ae0a9_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsource dash_adgroupsource_source_id_8def1c7c_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsource
    ADD CONSTRAINT dash_adgroupsource_source_id_8def1c7c_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_adgroupsourcesettings dash_adgroupsourceset_created_by_id_8e3462e5_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_adgroupsourcesettings
    ADD CONSTRAINT dash_adgroupsourceset_created_by_id_8e3462e5_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_agency dash_agency_modified_by_id_8a509311_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency
    ADD CONSTRAINT dash_agency_modified_by_id_8a509311_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_agency dash_agency_sales_representative_id_c9891192_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency
    ADD CONSTRAINT dash_agency_sales_representative_id_c9891192_fk_zemauth_user_id FOREIGN KEY (sales_representative_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_agency_users dash_agency_users_agency_id_b2d98b19_fk_dash_agency_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency_users
    ADD CONSTRAINT dash_agency_users_agency_id_b2d98b19_fk_dash_agency_id FOREIGN KEY (agency_id) REFERENCES dash_agency(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_agency_users dash_agency_users_user_id_c24f125c_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_agency_users
    ADD CONSTRAINT dash_agency_users_user_id_c24f125c_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_article dash_article_ad_group_id_e8e83acc_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_article
    ADD CONSTRAINT dash_article_ad_group_id_e8e83acc_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_audience dash_audience_created_by_id_2ac3dd70_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audience
    ADD CONSTRAINT dash_audience_created_by_id_2ac3dd70_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_audience dash_audience_pixel_id_f8d4b65b_fk_dash_conversionpixel_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audience
    ADD CONSTRAINT dash_audience_pixel_id_f8d4b65b_fk_dash_conversionpixel_id FOREIGN KEY (pixel_id) REFERENCES dash_conversionpixel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgethistory dash_budgethistory_budget_id_418d139d_fk_dash_budgetlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethistory_budget_id_418d139d_fk_dash_budgetlineitem_id FOREIGN KEY (budget_id) REFERENCES dash_budgetlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgethistory dash_budgethistory_created_by_id_7bd73304_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgethistory
    ADD CONSTRAINT dash_budgethistory_created_by_id_7bd73304_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetlineitem dash_budgetlineite_credit_id_6032abd6_fk_dash_creditlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlineite_credit_id_6032abd6_fk_dash_creditlineitem_id FOREIGN KEY (credit_id) REFERENCES dash_creditlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetlineitem dash_budgetlineitem_campaign_id_de5aaa38_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlineitem_campaign_id_de5aaa38_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_budgetlineitem dash_budgetlineitem_created_by_id_94a2d23a_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_budgetlineitem
    ADD CONSTRAINT dash_budgetlineitem_created_by_id_94a2d23a_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigngoal dash_camp_conversion_goal_id_a562cf2d_fk_dash_conversiongoal_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_camp_conversion_goal_id_a562cf2d_fk_dash_conversiongoal_id FOREIGN KEY (conversion_goal_id) REFERENCES dash_conversiongoal(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign dash_campaign_account_id_1c32102d_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_account_id_1c32102d_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigngoalvalue dash_campaign_campaign_goal_id_50abd25d_fk_dash_campaigngoal_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue
    ADD CONSTRAINT dash_campaign_campaign_goal_id_50abd25d_fk_dash_campaigngoal_id FOREIGN KEY (campaign_goal_id) REFERENCES dash_campaigngoal(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_groups dash_campaign_groups_campaign_id_f122fb4a_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_campaign_id_f122fb4a_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_groups dash_campaign_groups_group_id_9aee7593_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_groups
    ADD CONSTRAINT dash_campaign_groups_group_id_9aee7593_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign dash_campaign_modified_by_id_ffe81cbf_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign
    ADD CONSTRAINT dash_campaign_modified_by_id_ffe81cbf_fk_zemauth_user_id FOREIGN KEY (modified_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_users dash_campaign_users_campaign_id_1ac0ccc8_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_campaign_id_1ac0ccc8_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaign_users dash_campaign_users_user_id_0406e880_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaign_users
    ADD CONSTRAINT dash_campaign_users_user_id_0406e880_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigngoal dash_campaigngoal_campaign_id_ffc61ee8_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigngoal_campaign_id_ffc61ee8_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigngoal dash_campaigngoal_created_by_id_36b2347c_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoal
    ADD CONSTRAINT dash_campaigngoal_created_by_id_36b2347c_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaigngoalvalue dash_campaigngoalvalu_created_by_id_eb366170_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaigngoalvalue
    ADD CONSTRAINT dash_campaigngoalvalu_created_by_id_eb366170_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaignsettings dash_campaignse_campaign_manager_id_fca7b69b_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaignse_campaign_manager_id_fca7b69b_fk_zemauth_user_id FOREIGN KEY (campaign_manager_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaignsettings dash_campaignsettings_campaign_id_bf5994e4_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaignsettings_campaign_id_bf5994e4_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_campaignsettings dash_campaignsettings_created_by_id_066d74c5_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_campaignsettings
    ADD CONSTRAINT dash_campaignsettings_created_by_id_066d74c5_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentad dash_contentad_ad_group_id_1d1004e7_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_ad_group_id_1d1004e7_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentad dash_contentad_batch_id_88ee2abe_fk_dash_uploadbatch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentad
    ADD CONSTRAINT dash_contentad_batch_id_88ee2abe_fk_dash_uploadbatch_id FOREIGN KEY (batch_id) REFERENCES dash_uploadbatch(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentadcandidate dash_contentadcandidat_batch_id_d45612f1_fk_dash_uploadbatch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadcandidate
    ADD CONSTRAINT dash_contentadcandidat_batch_id_d45612f1_fk_dash_uploadbatch_id FOREIGN KEY (batch_id) REFERENCES dash_uploadbatch(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentadcandidate dash_contentadcandidate_ad_group_id_366c5cfa_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadcandidate
    ADD CONSTRAINT dash_contentadcandidate_ad_group_id_366c5cfa_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentadsource dash_contentadsourc_content_ad_id_4aae38ba_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsourc_content_ad_id_4aae38ba_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_contentadsource dash_contentadsource_source_id_c19d7d74_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_contentadsource
    ADD CONSTRAINT dash_contentadsource_source_id_c19d7d74_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversiongoal dash_conversiongoa_pixel_id_07d141b0_fk_dash_conversionpixel_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoa_pixel_id_07d141b0_fk_dash_conversionpixel_id FOREIGN KEY (pixel_id) REFERENCES dash_conversionpixel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversiongoal dash_conversiongoal_campaign_id_9b6738dd_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversiongoal
    ADD CONSTRAINT dash_conversiongoal_campaign_id_9b6738dd_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_conversionpixel dash_conversionpixel_account_id_2a1550f8_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_conversionpixel
    ADD CONSTRAINT dash_conversionpixel_account_id_2a1550f8_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_credithistory dash_credithistory_created_by_id_81384e00_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithistory_created_by_id_81384e00_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_credithistory dash_credithistory_credit_id_b593ac1c_fk_dash_creditlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_credithistory
    ADD CONSTRAINT dash_credithistory_credit_id_b593ac1c_fk_dash_creditlineitem_id FOREIGN KEY (credit_id) REFERENCES dash_creditlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditlineitem dash_creditlineitem_account_id_36f43384_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlineitem_account_id_36f43384_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditlineitem dash_creditlineitem_agency_id_886c51c2_fk_dash_agency_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlineitem_agency_id_886c51c2_fk_dash_agency_id FOREIGN KEY (agency_id) REFERENCES dash_agency(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_creditlineitem dash_creditlineitem_created_by_id_7c48ce5e_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_creditlineitem
    ADD CONSTRAINT dash_creditlineitem_created_by_id_7c48ce5e_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_defaultsourcesettings dash_defau_credentials_id_1d60e50c_fk_dash_sourcecredentials_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defau_credentials_id_1d60e50c_fk_dash_sourcecredentials_id FOREIGN KEY (credentials_id) REFERENCES dash_sourcecredentials(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_defaultsourcesettings dash_defaultsourcesettings_source_id_fe79a015_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_defaultsourcesettings
    ADD CONSTRAINT dash_defaultsourcesettings_source_id_fe79a015_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_demomapping dash_demomapping_real_account_id_92834e5c_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_demomapping
    ADD CONSTRAINT dash_demomapping_real_account_id_92834e5c_fk_dash_account_id FOREIGN KEY (real_account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport_filtered_agencies dash_exportrep_exportreport_id_b535bf0d_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_agencies
    ADD CONSTRAINT dash_exportrep_exportreport_id_b535bf0d_fk_dash_exportreport_id FOREIGN KEY (exportreport_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport_filtered_sources dash_exportrep_exportreport_id_b97d9bf3_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportrep_exportreport_id_b97d9bf3_fk_dash_exportreport_id FOREIGN KEY (exportreport_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport dash_exportreport_account_id_224e3f7a_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_account_id_224e3f7a_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport dash_exportreport_ad_group_id_ca9f09fa_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_ad_group_id_ca9f09fa_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport dash_exportreport_campaign_id_7c3c6bfc_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_campaign_id_7c3c6bfc_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport dash_exportreport_created_by_id_32f2da81_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport
    ADD CONSTRAINT dash_exportreport_created_by_id_32f2da81_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport_filtered_agencies dash_exportreport_filtered_agency_id_c7bfd046_fk_dash_agency_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_agencies
    ADD CONSTRAINT dash_exportreport_filtered_agency_id_c7bfd046_fk_dash_agency_id FOREIGN KEY (agency_id) REFERENCES dash_agency(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_exportreport_filtered_sources dash_exportreport_filtered_source_id_9bc51ede_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_exportreport_filtered_sources
    ADD CONSTRAINT dash_exportreport_filtered_source_id_9bc51ede_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_facebookaccount dash_facebookaccount_account_id_dd34b7c7_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_facebookaccount
    ADD CONSTRAINT dash_facebookaccount_account_id_dd34b7c7_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_history dash_history_account_id_ca6da4a9_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history
    ADD CONSTRAINT dash_history_account_id_ca6da4a9_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_history dash_history_ad_group_id_dfd6f805_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history
    ADD CONSTRAINT dash_history_ad_group_id_dfd6f805_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_history dash_history_agency_id_ff1479e9_fk_dash_agency_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history
    ADD CONSTRAINT dash_history_agency_id_ff1479e9_fk_dash_agency_id FOREIGN KEY (agency_id) REFERENCES dash_agency(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_history dash_history_campaign_id_dcf67e59_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history
    ADD CONSTRAINT dash_history_campaign_id_dcf67e59_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_history dash_history_created_by_id_dd83ae29_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_history
    ADD CONSTRAINT dash_history_created_by_id_dd83ae29_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherblacklist dash_publisherblacklis_campaign_id_2c77ce50_fk_dash_campaign_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklis_campaign_id_2c77ce50_fk_dash_campaign_id FOREIGN KEY (campaign_id) REFERENCES dash_campaign(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherblacklist dash_publisherblacklist_account_id_5500a754_fk_dash_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_account_id_5500a754_fk_dash_account_id FOREIGN KEY (account_id) REFERENCES dash_account(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherblacklist dash_publisherblacklist_ad_group_id_c2c0d6c5_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_ad_group_id_c2c0d6c5_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_publisherblacklist dash_publisherblacklist_source_id_a32359eb_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_publisherblacklist
    ADD CONSTRAINT dash_publisherblacklist_source_id_a32359eb_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_audiencerule dash_rule_audience_id_a6ee9274_fk_dash_audience_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_audiencerule
    ADD CONSTRAINT dash_rule_audience_id_a6ee9274_fk_dash_audience_id FOREIGN KEY (audience_id) REFERENCES dash_audience(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_scheduledexportreport dash_scheduledexport_report_id_40b4ac9f_fk_dash_exportreport_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_scheduledexport_report_id_40b4ac9f_fk_dash_exportreport_id FOREIGN KEY (report_id) REFERENCES dash_exportreport(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_scheduledexportreport dash_scheduledexportr_created_by_id_745a99f8_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_scheduledexportreport
    ADD CONSTRAINT dash_scheduledexportr_created_by_id_745a99f8_fk_zemauth_user_id FOREIGN KEY (created_by_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_source dash_source_source_type_id_150e6f78_fk_dash_sourcetype_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_source
    ADD CONSTRAINT dash_source_source_type_id_150e6f78_fk_dash_sourcetype_id FOREIGN KEY (source_type_id) REFERENCES dash_sourcetype(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sourcecredentials dash_sourcecredentials_source_id_5ac4ac70_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcecredentials
    ADD CONSTRAINT dash_sourcecredentials_source_id_5ac4ac70_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sourcetypepixel dash_sourcetypepi_source_type_id_a1a6947c_fk_dash_sourcetype_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetypepixel
    ADD CONSTRAINT dash_sourcetypepi_source_type_id_a1a6947c_fk_dash_sourcetype_id FOREIGN KEY (source_type_id) REFERENCES dash_sourcetype(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_sourcetypepixel dash_sourcetypepix_pixel_id_7fdd1e4f_fk_dash_conversionpixel_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_sourcetypepixel
    ADD CONSTRAINT dash_sourcetypepix_pixel_id_7fdd1e4f_fk_dash_conversionpixel_id FOREIGN KEY (pixel_id) REFERENCES dash_conversionpixel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dash_uploadbatch dash_uploadbatch_ad_group_id_99306811_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dash_uploadbatch
    ADD CONSTRAINT dash_uploadbatch_ad_group_id_99306811_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_content_type_id_c4bce8eb_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_content_type_id_c4bce8eb_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_refreshtoken oaut_access_token_id_775e84e8_fk_oauth2_provider_accesstoken_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_refreshtoken
    ADD CONSTRAINT oaut_access_token_id_775e84e8_fk_oauth2_provider_accesstoken_id FOREIGN KEY (access_token_id) REFERENCES oauth2_provider_accesstoken(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_accesstoken oauth2_provider_accesstoken_user_id_6e4c9a65_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_accesstoken
    ADD CONSTRAINT oauth2_provider_accesstoken_user_id_6e4c9a65_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_application oauth2_provider_application_user_id_79829054_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_application
    ADD CONSTRAINT oauth2_provider_application_user_id_79829054_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_grant oauth2_provider_grant_user_id_e8f62af8_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_grant
    ADD CONSTRAINT oauth2_provider_grant_user_id_e8f62af8_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_refreshtoken oauth2_provider_refreshtoke_user_id_da837fce_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_refreshtoken
    ADD CONSTRAINT oauth2_provider_refreshtoke_user_id_da837fce_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_refreshtoken oauth_application_id_2d1c311b_fk_oauth2_provider_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_refreshtoken
    ADD CONSTRAINT oauth_application_id_2d1c311b_fk_oauth2_provider_application_id FOREIGN KEY (application_id) REFERENCES oauth2_provider_application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_grant oauth_application_id_81923564_fk_oauth2_provider_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_grant
    ADD CONSTRAINT oauth_application_id_81923564_fk_oauth2_provider_application_id FOREIGN KEY (application_id) REFERENCES oauth2_provider_application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: oauth2_provider_accesstoken oauth_application_id_b22886e1_fk_oauth2_provider_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY oauth2_provider_accesstoken
    ADD CONSTRAINT oauth_application_id_b22886e1_fk_oauth2_provider_application_id FOREIGN KEY (application_id) REFERENCES oauth2_provider_application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadstats report_content_ad_source_id_b854568c_fk_dash_contentadsource_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT report_content_ad_source_id_b854568c_fk_dash_contentadsource_id FOREIGN KEY (content_ad_source_id) REFERENCES dash_contentadsource(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupgoalconversionstats reports_adgroupgoalconv_ad_group_id_ba616ded_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconv_ad_group_id_ba616ded_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupgoalconversionstats reports_adgroupgoalconvers_source_id_4fb849f4_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupgoalconversionstats
    ADD CONSTRAINT reports_adgroupgoalconvers_source_id_4fb849f4_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupstats reports_adgroupstats_ad_group_id_21cee625_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_ad_group_id_21cee625_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_adgroupstats reports_adgroupstats_source_id_75ecdd14_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_adgroupstats
    ADD CONSTRAINT reports_adgroupstats_source_id_75ecdd14_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlestats reports_articlestats_ad_group_id_e534ddd6_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_ad_group_id_e534ddd6_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlestats reports_articlestats_article_id_efbb7a68_fk_dash_article_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_article_id_efbb7a68_fk_dash_article_id FOREIGN KEY (article_id) REFERENCES dash_article(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_articlestats reports_articlestats_source_id_7037cd45_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_articlestats
    ADD CONSTRAINT reports_articlestats_source_id_7037cd45_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_budgetdailystatement reports_budgetdail_budget_id_57f15b8f_fk_dash_budgetlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatement
    ADD CONSTRAINT reports_budgetdail_budget_id_57f15b8f_fk_dash_budgetlineitem_id FOREIGN KEY (budget_id) REFERENCES dash_budgetlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_budgetdailystatementk1 reports_budgetdail_budget_id_74ec6e2b_fk_dash_budgetlineitem_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_budgetdailystatementk1
    ADD CONSTRAINT reports_budgetdail_budget_id_74ec6e2b_fk_dash_budgetlineitem_id FOREIGN KEY (budget_id) REFERENCES dash_budgetlineitem(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadgoalconversionstats reports_contentadgo_content_ad_id_77697a53_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgo_content_ad_id_77697a53_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadgoalconversionstats reports_contentadgoalconve_source_id_1792f0e7_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadgoalconversionstats
    ADD CONSTRAINT reports_contentadgoalconve_source_id_1792f0e7_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadpostclickstats reports_contentadpo_content_ad_id_771cc69a_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpo_content_ad_id_771cc69a_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadpostclickstats reports_contentadpostclick_source_id_1e4269d1_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadpostclickstats
    ADD CONSTRAINT reports_contentadpostclick_source_id_1e4269d1_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadstats reports_contentadst_content_ad_id_7d2b45a7_fk_dash_contentad_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadst_content_ad_id_7d2b45a7_fk_dash_contentad_id FOREIGN KEY (content_ad_id) REFERENCES dash_contentad(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_contentadstats reports_contentadstats_source_id_8baa356c_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_contentadstats
    ADD CONSTRAINT reports_contentadstats_source_id_8baa356c_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconversionstats reports_goalconversions_ad_group_id_314032d3_fk_dash_adgroup_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversions_ad_group_id_314032d3_fk_dash_adgroup_id FOREIGN KEY (ad_group_id) REFERENCES dash_adgroup(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconversionstats reports_goalconversionst_article_id_b91d10b3_fk_dash_article_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionst_article_id_b91d10b3_fk_dash_article_id FOREIGN KEY (article_id) REFERENCES dash_article(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_goalconversionstats reports_goalconversionstat_source_id_18bb273e_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_goalconversionstats
    ADD CONSTRAINT reports_goalconversionstat_source_id_18bb273e_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reports_supplyreportrecipient reports_supplyreportrecipi_source_id_865b4b0c_fk_dash_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY reports_supplyreportrecipient
    ADD CONSTRAINT reports_supplyreportrecipi_source_id_865b4b0c_fk_dash_source_id FOREIGN KEY (source_id) REFERENCES dash_source(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: restapi_reportjob restapi_reportjob_user_id_9145a152_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY restapi_reportjob
    ADD CONSTRAINT restapi_reportjob_user_id_9145a152_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_internalgroup zemauth_internalgroup_group_id_e47b2df0_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_internalgroup
    ADD CONSTRAINT zemauth_internalgroup_group_id_e47b2df0_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_groups zemauth_user_groups_group_id_15e5c1d2_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_group_id_15e5c1d2_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_groups zemauth_user_groups_user_id_5707f44e_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_groups
    ADD CONSTRAINT zemauth_user_groups_user_id_5707f44e_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_user_permissions zemauth_user_user__permission_id_3e849c88_fk_auth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user__permission_id_3e849c88_fk_auth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: zemauth_user_user_permissions zemauth_user_user_permissio_user_id_cfd35827_fk_zemauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY zemauth_user_user_permissions
    ADD CONSTRAINT zemauth_user_user_permissio_user_id_cfd35827_fk_zemauth_user_id FOREIGN KEY (user_id) REFERENCES zemauth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

