-- This file includes all UDF functions that need to be applied on Redshift cluster.

/*
Sums key values of jsons separated by a delimiter. Useful with LISTAGG aggregate function. LISTAGG is used
as a workaround until Redshift adds support for aggregate UDF functions.

IMPORTANT: Make sure you use the same delimiter as for LISTAGG.

Example:
  SELECT
    ad_group_id,
    json_dict_sum(LISTAGG(conversions, '\n'), '\n')
  FROM postclickstats
  WHERE date='2016-05-23'
  GROUP BY ad_group_id;
*/
CREATE OR REPLACE FUNCTION json_dict_sum (a varchar(max), delimiter varchar(2)) RETURNS varchar(max) IMMUTABLE as $$
      import json
      if not a:
        return ""

      d = {}
      for line in a.split(delimiter):
          line = line.strip()
          if not line:
             continue

          dicts = json.loads(line)
          for k, v in dicts.iteritems():
              if k not in d:
                 d[k] = 0
              d[k] += v

      return json.dumps(d)
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_source_slug (source_slug varchar(130)) RETURNS varchar(127) IMMUTABLE as $$
      if not source_slug:
          return None

      if source_slug.startswith('b1_'):
          return source_slug[3:]
      return source_slug
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_device_type (device_type integer) RETURNS int2 IMMUTABLE as $$
      /* OpenRTB Device Type mapping */
      if device_type == 4:
          return 3  # constants.DeviceType.MOBILE
      elif device_type == 2:
          return 1  # constants.DeviceType.DESKTOP
      elif device_type == 5:
          return 2  # constants.DeviceType.TABLET
      return 0  # constants.DeviceType.UNDEFINED
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_country (country varchar(255)) RETURNS varchar(2) IMMUTABLE as $$
      if country and len(country) == 2:
          return country.upper()
      return None
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_state (state varchar(255)) RETURNS varchar(5) IMMUTABLE as $$
      if state and len(state) <= 5:
          return state.upper()
      return None
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_dma (dma integer) RETURNS int2 IMMUTABLE as $$
      if 499 < dma < 1000:
          return dma
      return None
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_age (age varchar(255)) RETURNS int2 IMMUTABLE as $$
      if not age:
          return 0  # constants.AgeGroup.UNDEFINED

      age = age.strip()
      if age == '18-20':
          return 1  # constants.AgeGroup.AGE_18_20
      elif age == '21-29':
          return 2  # constants.AgeGroup.AGE_21_29
      elif age == '30-39':
          return 3  # constants.AgeGroup.AGE_30_39
      elif age == '40-49':
          return 4  # constants.AgeGroup.AGE_40_49
      elif age == '50-64':
          return 5  # constants.AgeGroup.AGE_50_64
      elif age == '65+':
          return 6  # constants.AgeGroup.AGE_65_MORE
      return 0  # constants.AgeGroup.UNDEFINED
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_gender (gender varchar(255)) RETURNS int2 IMMUTABLE as $$
      if not gender:
          return 0  # constants.Gender.UNDEFINED

      gender = gender.strip()
      if gender == 'female':
          return 2  # constants.Gender.WOMEN
      elif gender == 'male':
          return 1  # constants.Gender.MEN
      return 0  # constants.Gender.UNDEFINED
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION extract_age_gender (age varchar(255), gender varchar(255)) RETURNS int2 IMMUTABLE as $$
      def extract_age(_age):
          if not _age:
              return 0  # constants.AgeGroup.UNDEFINED

          _age = _age.strip()
          if _age == '18-20':
              return 1  # constants.AgeGroup.AGE_18_20
          elif _age == '21-29':
              return 2  # constants.AgeGroup.AGE_21_29
          elif _age == '30-39':
              return 3  # constants.AgeGroup.AGE_30_39
          elif _age == '40-49':
              return 4  # constants.AgeGroup.AGE_40_49
          elif _age == '50-64':
              return 5  # constants.AgeGroup.AGE_50_64
          elif _age == '65+':
              return 6  # constants.AgeGroup.AGE_65_MORE
          return 0  # constants.AgeGroup.UNDEFINED

      def extract_gender(_gender):
          if not _gender:
              return 0  # constants.Gender.UNDEFINED

          _gender = _gender.strip()
          if _gender == 'female':
              return 2  # constants.Gender.WOMEN
          elif _gender == 'male':
              return 1  # constants.Gender.MEN
          return 0  # constants.Gender.UNDEFINED


      age = extract_age(age)
      gender = extract_gender(gender)

      mapping = {
          2: {  # constants.Gender.WOMEN
              1: 2,
              2: 5,
              3: 8,
              4: 11,
              5: 14,
              6: 17,
              # constants.AgeGroup.AGE_18_20: constants.AgeGenderGroup.AGE_18_20_WOMEN,
              # constants.AgeGroup.AGE_21_29: constants.AgeGenderGroup.AGE_21_29_WOMEN,
              # constants.AgeGroup.AGE_30_39: constants.AgeGenderGroup.AGE_30_39_WOMEN,
              # constants.AgeGroup.AGE_40_49: constants.AgeGenderGroup.AGE_40_49_WOMEN,
              # constants.AgeGroup.AGE_50_64: constants.AgeGenderGroup.AGE_50_64_WOMEN,
              # constants.AgeGroup.AGE_65_MORE: constants.AgeGenderGroup.AGE_65_MORE_WOMEN,
          },
          1: {  # constants.Gender.MEN
              1: 1,
              2: 4,
              3: 7,
              4: 10,
              5: 13,
              6: 16,
              # constants.AgeGroup.AGE_18_20: constants.AgeGenderGroup.AGE_18_20_MEN,
              # constants.AgeGroup.AGE_21_29: constants.AgeGenderGroup.AGE_21_29_MEN,
              # constants.AgeGroup.AGE_30_39: constants.AgeGenderGroup.AGE_30_39_MEN,
              # constants.AgeGroup.AGE_40_49: constants.AgeGenderGroup.AGE_40_49_MEN,
              # constants.AgeGroup.AGE_50_64: constants.AgeGenderGroup.AGE_50_64_MEN,
              # constants.AgeGroup.AGE_65_MORE: constants.AgeGenderGroup.AGE_65_MORE_MEN,
          },
          0: {  # constants.Gender.UNDEFINED
              1: 3,
              2: 6,
              3: 9,
              4: 12,
              5: 15,
              6: 18,
              # constants.AgeGroup.AGE_18_20: constants.AgeGenderGroup.AGE_18_20_UNDEFINED,
              # constants.AgeGroup.AGE_21_29: constants.AgeGenderGroup.AGE_21_29_UNDEFINED,
              # constants.AgeGroup.AGE_30_39: constants.AgeGenderGroup.AGE_30_39_UNDEFINED,
              # constants.AgeGroup.AGE_40_49: constants.AgeGenderGroup.AGE_40_49_UNDEFINED,
              # constants.AgeGroup.AGE_50_64: constants.AgeGenderGroup.AGE_50_64_UNDEFINED,
              # constants.AgeGroup.AGE_65_MORE: constants.AgeGenderGroup.AGE_65_MORE_UNDEFINED,
          },
      }

      if gender in mapping:
          return mapping[gender].get(age, 0)  # constants.AgeGenderGroup.UNDEFINED

      return 0  # constants.AgeGenderGroup.UNDEFINED
$$ LANGUAGE plpythonu;
