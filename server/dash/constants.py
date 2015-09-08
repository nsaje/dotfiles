from utils.constant_base import ConstantBase
from dash import regions


class AdGroupSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class AdGroupRunningStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Running',
        INACTIVE: 'Stopped'
    }


class AdGroupSourceSettingsState(ConstantBase):
    # keep in sync with zwei
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class AdTargetDevice(ConstantBase):
    DESKTOP = 'desktop'
    MOBILE = 'mobile'

    _VALUES = {
        DESKTOP: 'Desktop',
        MOBILE: 'Mobile'
    }


class AdTargetLocation(ConstantBase):
    _VALUES = dict(regions.COUNTRY_BY_CODE.items() + regions.DMA_BY_CODE.items())

    @classmethod
    def get_choices(cls):
        return cls._VALUES.items()


class ContentAdSubmissionStatus(ConstantBase):
    NOT_SUBMITTED = -1
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    LIMIT_REACHED = 4

    _VALUES = {
        NOT_SUBMITTED: 'Not submitted',
        PENDING: 'Pending',
        APPROVED: 'Approved',
        REJECTED: 'Rejected',
        LIMIT_REACHED: 'Limit reached',
    }


class ContentAdSourceState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class IABCategory(ConstantBase):
    IAB1 = "IAB1"
    IAB1_1 = "IAB1_1"
    IAB1_2 = "IAB1_2"
    IAB1_3 = "IAB1_3"
    IAB1_4 = "IAB1_4"
    IAB1_5 = "IAB1_5"
    IAB1_6 = "IAB1_6"
    IAB1_7 = "IAB1_7"
    IAB2 = "IAB2"
    IAB2_1 = "IAB2_1"
    IAB2_2 = "IAB2_2"
    IAB2_3 = "IAB2_3"
    IAB2_4 = "IAB2_4"
    IAB2_5 = "IAB2_5"
    IAB2_6 = "IAB2_6"
    IAB2_7 = "IAB2_7"
    IAB2_8 = "IAB2_8"
    IAB2_9 = "IAB2_9"
    IAB2_10 = "IAB2_10"
    IAB2_11 = "IAB2_11"
    IAB2_12 = "IAB2_12"
    IAB2_13 = "IAB2_13"
    IAB2_14 = "IAB2_14"
    IAB2_15 = "IAB2_15"
    IAB2_16 = "IAB2_16"
    IAB2_17 = "IAB2_17"
    IAB2_18 = "IAB2_18"
    IAB2_19 = "IAB2_19"
    IAB2_20 = "IAB2_20"
    IAB2_21 = "IAB2_21"
    IAB2_22 = "IAB2_22"
    IAB2_23 = "IAB2_23"
    IAB3 = "IAB3"
    IAB3_1 = "IAB3_1"
    IAB3_2 = "IAB3_2"
    IAB3_3 = "IAB3_3"
    IAB3_4 = "IAB3_4"
    IAB3_5 = "IAB3_5"
    IAB3_6 = "IAB3_6"
    IAB3_7 = "IAB3_7"
    IAB3_8 = "IAB3_8"
    IAB3_9 = "IAB3_9"
    IAB3_10 = "IAB3_10"
    IAB3_11 = "IAB3_11"
    IAB3_12 = "IAB3_12"
    IAB4 = "IAB4"
    IAB4_1 = "IAB4_1"
    IAB4_2 = "IAB4_2"
    IAB4_3 = "IAB4_3"
    IAB4_4 = "IAB4_4"
    IAB4_5 = "IAB4_5"
    IAB4_6 = "IAB4_6"
    IAB4_7 = "IAB4_7"
    IAB4_8 = "IAB4_8"
    IAB4_9 = "IAB4_9"
    IAB4_10 = "IAB4_10"
    IAB4_11 = "IAB4_11"
    IAB5 = "IAB5"
    IAB5_1 = "IAB5_1"
    IAB5_2 = "IAB5_2"
    IAB5_3 = "IAB5_3"
    IAB5_4 = "IAB5_4"
    IAB5_5 = "IAB5_5"
    IAB5_6 = "IAB5_6"
    IAB5_7 = "IAB5_7"
    IAB5_8 = "IAB5_8"
    IAB5_9 = "IAB5_9"
    IAB5_10 = "IAB5_10"
    IAB5_11 = "IAB5_11"
    IAB5_12 = "IAB5_12"
    IAB5_13 = "IAB5_13"
    IAB5_14 = "IAB5_14"
    IAB5_15 = "IAB5_15"
    IAB6 = "IAB6"
    IAB6_1 = "IAB6_1"
    IAB6_2 = "IAB6_2"
    IAB6_3 = "IAB6_3"
    IAB6_4 = "IAB6_4"
    IAB6_5 = "IAB6_5"
    IAB6_6 = "IAB6_6"
    IAB6_7 = "IAB6_7"
    IAB6_8 = "IAB6_8"
    IAB6_9 = "IAB6_9"
    IAB7 = "IAB7"
    IAB7_1 = "IAB7_1"
    IAB7_2 = "IAB7_2"
    IAB7_3 = "IAB7_3"
    IAB7_4 = "IAB7_4"
    IAB7_5 = "IAB7_5"
    IAB7_6 = "IAB7_6"
    IAB7_7 = "IAB7_7"
    IAB7_8 = "IAB7_8"
    IAB7_9 = "IAB7_9"
    IAB7_10 = "IAB7_10"
    IAB7_11 = "IAB7_11"
    IAB7_12 = "IAB7_12"
    IAB7_13 = "IAB7_13"
    IAB7_14 = "IAB7_14"
    IAB7_15 = "IAB7_15"
    IAB7_16 = "IAB7_16"
    IAB7_17 = "IAB7_17"
    IAB7_18 = "IAB7_18"
    IAB7_19 = "IAB7_19"
    IAB7_20 = "IAB7_20"
    IAB7_21 = "IAB7_21"
    IAB7_22 = "IAB7_22"
    IAB7_23 = "IAB7_23"
    IAB7_24 = "IAB7_24"
    IAB7_25 = "IAB7_25"
    IAB7_26 = "IAB7_26"
    IAB7_27 = "IAB7_27"
    IAB7_28 = "IAB7_28"
    IAB7_29 = "IAB7_29"
    IAB7_30 = "IAB7_30"
    IAB7_31 = "IAB7_31"
    IAB7_32 = "IAB7_32"
    IAB7_33 = "IAB7_33"
    IAB7_34 = "IAB7_34"
    IAB7_35 = "IAB7_35"
    IAB7_36 = "IAB7_36"
    IAB7_37 = "IAB7_37"
    IAB7_38 = "IAB7_38"
    IAB7_39 = "IAB7_39"
    IAB7_40 = "IAB7_40"
    IAB7_41 = "IAB7_41"
    IAB7_42 = "IAB7_42"
    IAB7_43 = "IAB7_43"
    IAB7_44 = "IAB7_44"
    IAB7_45 = "IAB7_45"
    IAB8 = "IAB8"
    IAB8_1 = "IAB8_1"
    IAB8_2 = "IAB8_2"
    IAB8_3 = "IAB8_3"
    IAB8_4 = "IAB8_4"
    IAB8_5 = "IAB8_5"
    IAB8_6 = "IAB8_6"
    IAB8_7 = "IAB8_7"
    IAB8_8 = "IAB8_8"
    IAB8_9 = "IAB8_9"
    IAB8_10 = "IAB8_10"
    IAB8_11 = "IAB8_11"
    IAB8_12 = "IAB8_12"
    IAB8_13 = "IAB8_13"
    IAB8_14 = "IAB8_14"
    IAB8_15 = "IAB8_15"
    IAB8_16 = "IAB8_16"
    IAB8_17 = "IAB8_17"
    IAB8_18 = "IAB8_18"
    IAB9 = "IAB9"
    IAB9_1 = "IAB9_1"
    IAB9_2 = "IAB9_2"
    IAB9_3 = "IAB9_3"
    IAB9_4 = "IAB9_4"
    IAB9_5 = "IAB9_5"
    IAB9_6 = "IAB9_6"
    IAB9_7 = "IAB9_7"
    IAB9_8 = "IAB9_8"
    IAB9_9 = "IAB9_9"
    IAB9_10 = "IAB9_10"
    IAB9_11 = "IAB9_11"
    IAB9_12 = "IAB9_12"
    IAB9_13 = "IAB9_13"
    IAB9_14 = "IAB9_14"
    IAB9_15 = "IAB9_15"
    IAB9_16 = "IAB9_16"
    IAB9_17 = "IAB9_17"
    IAB9_18 = "IAB9_18"
    IAB9_19 = "IAB9_19"
    IAB9_20 = "IAB9_20"
    IAB9_21 = "IAB9_21"
    IAB9_22 = "IAB9_22"
    IAB9_23 = "IAB9_23"
    IAB9_24 = "IAB9_24"
    IAB9_25 = "IAB9_25"
    IAB9_26 = "IAB9_26"
    IAB9_27 = "IAB9_27"
    IAB9_28 = "IAB9_28"
    IAB9_29 = "IAB9_29"
    IAB9_30 = "IAB9_30"
    IAB9_31 = "IAB9_31"
    IAB10 = "IAB10"
    IAB10_1 = "IAB10_1"
    IAB10_2 = "IAB10_2"
    IAB10_3 = "IAB10_3"
    IAB10_4 = "IAB10_4"
    IAB10_5 = "IAB10_5"
    IAB10_6 = "IAB10_6"
    IAB10_7 = "IAB10_7"
    IAB10_8 = "IAB10_8"
    IAB10_9 = "IAB10_9"
    IAB11 = "IAB11"
    IAB11_1 = "IAB11_1"
    IAB11_2 = "IAB11_2"
    IAB11_3 = "IAB11_3"
    IAB11_4 = "IAB11_4"
    IAB11_5 = "IAB11_5"
    IAB12 = "IAB12"
    IAB12_1 = "IAB12_1"
    IAB12_2 = "IAB12_2"
    IAB12_3 = "IAB12_3"
    IAB13 = "IAB13"
    IAB13_1 = "IAB13_1"
    IAB13_2 = "IAB13_2"
    IAB13_3 = "IAB13_3"
    IAB13_4 = "IAB13_4"
    IAB13_5 = "IAB13_5"
    IAB13_6 = "IAB13_6"
    IAB13_7 = "IAB13_7"
    IAB13_8 = "IAB13_8"
    IAB13_9 = "IAB13_9"
    IAB13_10 = "IAB13_10"
    IAB13_11 = "IAB13_11"
    IAB13_12 = "IAB13_12"
    IAB14 = "IAB14"
    IAB14_1 = "IAB14_1"
    IAB14_2 = "IAB14_2"
    IAB14_3 = "IAB14_3"
    IAB14_4 = "IAB14_4"
    IAB14_5 = "IAB14_5"
    IAB14_6 = "IAB14_6"
    IAB14_7 = "IAB14_7"
    IAB14_8 = "IAB14_8"
    IAB15 = "IAB15"
    IAB15_1 = "IAB15_1"
    IAB15_2 = "IAB15_2"
    IAB15_3 = "IAB15_3"
    IAB15_4 = "IAB15_4"
    IAB15_5 = "IAB15_5"
    IAB15_6 = "IAB15_6"
    IAB15_7 = "IAB15_7"
    IAB15_8 = "IAB15_8"
    IAB15_9 = "IAB15_9"
    IAB15_10 = "IAB15_10"
    IAB16 = "IAB16"
    IAB16_1 = "IAB16_1"
    IAB16_2 = "IAB16_2"
    IAB16_3 = "IAB16_3"
    IAB16_4 = "IAB16_4"
    IAB16_5 = "IAB16_5"
    IAB16_6 = "IAB16_6"
    IAB16_7 = "IAB16_7"
    IAB17 = "IAB17"
    IAB17_1 = "IAB17_1"
    IAB17_2 = "IAB17_2"
    IAB17_3 = "IAB17_3"
    IAB17_4 = "IAB17_4"
    IAB17_5 = "IAB17_5"
    IAB17_6 = "IAB17_6"
    IAB17_7 = "IAB17_7"
    IAB17_8 = "IAB17_8"
    IAB17_9 = "IAB17_9"
    IAB17_10 = "IAB17_10"
    IAB17_11 = "IAB17_11"
    IAB17_12 = "IAB17_12"
    IAB17_13 = "IAB17_13"
    IAB17_14 = "IAB17_14"
    IAB17_15 = "IAB17_15"
    IAB17_16 = "IAB17_16"
    IAB17_17 = "IAB17_17"
    IAB17_18 = "IAB17_18"
    IAB17_19 = "IAB17_19"
    IAB17_20 = "IAB17_20"
    IAB17_21 = "IAB17_21"
    IAB17_22 = "IAB17_22"
    IAB17_23 = "IAB17_23"
    IAB17_24 = "IAB17_24"
    IAB17_25 = "IAB17_25"
    IAB17_26 = "IAB17_26"
    IAB17_27 = "IAB17_27"
    IAB17_28 = "IAB17_28"
    IAB17_29 = "IAB17_29"
    IAB17_30 = "IAB17_30"
    IAB17_31 = "IAB17_31"
    IAB17_32 = "IAB17_32"
    IAB17_33 = "IAB17_33"
    IAB17_34 = "IAB17_34"
    IAB17_35 = "IAB17_35"
    IAB17_36 = "IAB17_36"
    IAB17_37 = "IAB17_37"
    IAB17_38 = "IAB17_38"
    IAB17_39 = "IAB17_39"
    IAB17_40 = "IAB17_40"
    IAB17_41 = "IAB17_41"
    IAB17_42 = "IAB17_42"
    IAB17_43 = "IAB17_43"
    IAB17_44 = "IAB17_44"
    IAB18 = "IAB18"
    IAB18_1 = "IAB18_1"
    IAB18_2 = "IAB18_2"
    IAB18_3 = "IAB18_3"
    IAB18_4 = "IAB18_4"
    IAB18_5 = "IAB18_5"
    IAB18_6 = "IAB18_6"
    IAB19 = "IAB19"
    IAB19_1 = "IAB19_1"
    IAB19_2 = "IAB19_2"
    IAB19_3 = "IAB19_3"
    IAB19_4 = "IAB19_4"
    IAB19_5 = "IAB19_5"
    IAB19_6 = "IAB19_6"
    IAB19_7 = "IAB19_7"
    IAB19_8 = "IAB19_8"
    IAB19_9 = "IAB19_9"
    IAB19_10 = "IAB19_10"
    IAB19_11 = "IAB19_11"
    IAB19_12 = "IAB19_12"
    IAB19_13 = "IAB19_13"
    IAB19_14 = "IAB19_14"
    IAB19_15 = "IAB19_15"
    IAB19_16 = "IAB19_16"
    IAB19_17 = "IAB19_17"
    IAB19_18 = "IAB19_18"
    IAB19_19 = "IAB19_19"
    IAB19_20 = "IAB19_20"
    IAB19_21 = "IAB19_21"
    IAB19_22 = "IAB19_22"
    IAB19_23 = "IAB19_23"
    IAB19_24 = "IAB19_24"
    IAB19_25 = "IAB19_25"
    IAB19_26 = "IAB19_26"
    IAB19_27 = "IAB19_27"
    IAB19_28 = "IAB19_28"
    IAB19_29 = "IAB19_29"
    IAB19_30 = "IAB19_30"
    IAB19_31 = "IAB19_31"
    IAB19_32 = "IAB19_32"
    IAB19_33 = "IAB19_33"
    IAB19_34 = "IAB19_34"
    IAB19_35 = "IAB19_35"
    IAB19_36 = "IAB19_36"
    IAB20 = "IAB20"
    IAB20_1 = "IAB20_1"
    IAB20_2 = "IAB20_2"
    IAB20_3 = "IAB20_3"
    IAB20_4 = "IAB20_4"
    IAB20_5 = "IAB20_5"
    IAB20_6 = "IAB20_6"
    IAB20_7 = "IAB20_7"
    IAB20_8 = "IAB20_8"
    IAB20_9 = "IAB20_9"
    IAB20_10 = "IAB20_10"
    IAB20_11 = "IAB20_11"
    IAB20_12 = "IAB20_12"
    IAB20_13 = "IAB20_13"
    IAB20_14 = "IAB20_14"
    IAB20_15 = "IAB20_15"
    IAB20_16 = "IAB20_16"
    IAB20_17 = "IAB20_17"
    IAB20_18 = "IAB20_18"
    IAB20_19 = "IAB20_19"
    IAB20_20 = "IAB20_20"
    IAB20_21 = "IAB20_21"
    IAB20_22 = "IAB20_22"
    IAB20_23 = "IAB20_23"
    IAB20_24 = "IAB20_24"
    IAB20_25 = "IAB20_25"
    IAB20_26 = "IAB20_26"
    IAB20_27 = "IAB20_27"
    IAB21 = "IAB21"
    IAB21_1 = "IAB21_1"
    IAB21_2 = "IAB21_2"
    IAB21_3 = "IAB21_3"
    IAB22 = "IAB22"
    IAB22_1 = "IAB22_1"
    IAB22_2 = "IAB22_2"
    IAB22_3 = "IAB22_3"
    IAB22_4 = "IAB22_4"
    IAB23 = "IAB23"
    IAB23_1 = "IAB23_1"
    IAB23_2 = "IAB23_2"
    IAB23_3 = "IAB23_3"
    IAB23_4 = "IAB23_4"
    IAB23_5 = "IAB23_5"
    IAB23_6 = "IAB23_6"
    IAB23_7 = "IAB23_7"
    IAB23_8 = "IAB23_8"
    IAB23_9 = "IAB23_9"
    IAB23_10 = "IAB23_10"
    IAB24 = "IAB24"
    IAB25 = "IAB25"
    IAB25_1 = "IAB25_1"
    IAB25_2 = "IAB25_2"
    IAB25_3 = "IAB25_3"
    IAB25_4 = "IAB25_4"
    IAB25_5 = "IAB25_5"
    IAB25_6 = "IAB25_6"
    IAB25_7 = "IAB25_7"
    IAB26 = "IAB26"
    IAB26_1 = "IAB26_1"
    IAB26_2 = "IAB26_2"
    IAB26_3 = "IAB26_3"
    IAB26_4 = "IAB26_4"

    _VALUES = {
        IAB1: "Arts & Entertainment",
        IAB1_1: "Books & Literature",
        IAB1_2: "Celebrity Fan/Gossip",
        IAB1_3: "Fine Art",
        IAB1_4: "Humor",
        IAB1_5: "Movies",
        IAB1_6: "Music",
        IAB1_7: "Television",
        IAB2: "Automotive",
        IAB2_1: "Auto Parts",
        IAB2_2: "Auto Repair",
        IAB2_3: "Buying/Selling Cars",
        IAB2_4: "Car Culture",
        IAB2_5: "Certified Pre-Owned",
        IAB2_6: "Convertible",
        IAB2_7: "Coupe",
        IAB2_8: "Crossover",
        IAB2_9: "Diesel",
        IAB2_10: "Electric Vehicle",
        IAB2_11: "Hatchback",
        IAB2_12: "Hybrid",
        IAB2_13: "Luxury",
        IAB2_14: "MiniVan",
        IAB2_15: "Mororcycles",
        IAB2_16: "Off-Road Vehicles",
        IAB2_17: "Performance Vehicles",
        IAB2_18: "Pickup",
        IAB2_19: "Road-Side Assistance",
        IAB2_20: "Sedan",
        IAB2_21: "Trucks & Accessories",
        IAB2_22: "Vintage Cars",
        IAB2_23: "Wagon",
        IAB3: "Business",
        IAB3_1: "Advertising",
        IAB3_2: "Agriculture",
        IAB3_3: "Biotech/Biomedical",
        IAB3_4: "Business Software",
        IAB3_5: "Construction",
        IAB3_6: "Forestry",
        IAB3_7: "Government",
        IAB3_8: "Green Solutions",
        IAB3_9: "Human Resources",
        IAB3_10: "Logistics",
        IAB3_11: "Marketing",
        IAB3_12: "Metals",
        IAB4: "Careers",
        IAB4_1: "Career Planning",
        IAB4_2: "College",
        IAB4_3: "Financial Aid",
        IAB4_4: "Job Fairs",
        IAB4_5: "Job Search",
        IAB4_6: "Resume Writing/Advice",
        IAB4_7: "Nursing",
        IAB4_8: "Scholarships",
        IAB4_9: "Telecommuting",
        IAB4_10: "U.S. Military",
        IAB4_11: "Career Advice",
        IAB5: "Education",
        IAB5_1: "7-12 Education",
        IAB5_2: "Adult Education",
        IAB5_3: "Art History",
        IAB5_4: "Colledge Administration",
        IAB5_5: "College Life",
        IAB5_6: "Distance Learning",
        IAB5_7: "English as a 2nd Language",
        IAB5_8: "Language Learning",
        IAB5_9: "Graduate School",
        IAB5_10: "Homeschooling",
        IAB5_11: "Homework/Study Tips",
        IAB5_12: "K-6 Educators",
        IAB5_13: "Private School",
        IAB5_14: "Special Education",
        IAB5_15: "Studying Business",
        IAB6: "Family & Parenting",
        IAB6_1: "Adoption",
        IAB6_2: "Babies & Toddlers",
        IAB6_3: "Daycare/Pre School",
        IAB6_4: "Family Internet",
        IAB6_5: "Parenting - K-6 Kids",
        IAB6_6: "Parenting teens",
        IAB6_7: "Pregnancy",
        IAB6_8: "Special Needs Kids",
        IAB6_9: "Eldercare",
        IAB7: "Health & Fitness",
        IAB7_1: "Exercise",
        IAB7_2: "A.D.D.",
        IAB7_3: "AIDS/HIV",
        IAB7_4: "Allergies",
        IAB7_5: "Alternative Medicine",
        IAB7_6: "Arthritis",
        IAB7_7: "Asthma",
        IAB7_8: "Autism/PDD",
        IAB7_9: "Bipolar Disorder",
        IAB7_10: "Brain Tumor",
        IAB7_11: "Cancer",
        IAB7_12: "Cholesterol",
        IAB7_13: "Chronic Fatigue Syndrome",
        IAB7_14: "Chronic Pain",
        IAB7_15: "Cold & Flu",
        IAB7_16: "Deafness",
        IAB7_17: "Dental Care",
        IAB7_18: "Depression",
        IAB7_19: "Dermatology",
        IAB7_20: "Diabetes",
        IAB7_21: "Epilepsy",
        IAB7_22: "GERD/Acid Reflux",
        IAB7_23: "Headaches/Migraines",
        IAB7_24: "Heart Disease",
        IAB7_25: "Herbs for Health",
        IAB7_26: "Holistic Healing",
        IAB7_27: "IBS/Crohn's Disease",
        IAB7_28: "Incest/Abuse Support",
        IAB7_29: "Incontinence",
        IAB7_30: "Infertility",
        IAB7_31: "Men's Health",
        IAB7_32: "Nutrition",
        IAB7_33: "Orthopedics",
        IAB7_34: "Panic/Anxiety Disorders",
        IAB7_35: "Pediatrics",
        IAB7_36: "Physical Therapy",
        IAB7_37: "Psychology/Psychiatry",
        IAB7_38: "Senor Health",
        IAB7_39: "Sexuality",
        IAB7_40: "Sleep Disorders",
        IAB7_41: "Smoking Cessation",
        IAB7_42: "Substance Abuse",
        IAB7_43: "Thyroid Disease",
        IAB7_44: "Weight Loss",
        IAB7_45: "Women's Health",
        IAB8: "Food & Drink",
        IAB8_1: "American Cuisine",
        IAB8_2: "Barbecues & Grilling",
        IAB8_3: "Cajun/Creole",
        IAB8_4: "Chinese Cuisine",
        IAB8_5: "Cocktails/Beer",
        IAB8_6: "Coffee/Tea",
        IAB8_7: "Cuisine-Specific",
        IAB8_8: "Desserts & Baking",
        IAB8_9: "Dining Out",
        IAB8_10: "Food Allergies",
        IAB8_11: "French Cuisine",
        IAB8_12: "Health/Lowfat Cooking",
        IAB8_13: "Italian Cuisine",
        IAB8_14: "Japanese Cuisine",
        IAB8_15: "Mexican Cuisine",
        IAB8_16: "Vegan",
        IAB8_17: "Vegetarian",
        IAB8_18: "Wine",
        IAB9: "Hobbies & Interests",
        IAB9_1: "Art/Technology",
        IAB9_2: "Arts & Crafts",
        IAB9_3: "Beadwork",
        IAB9_4: "Birdwatching",
        IAB9_5: "Board Games/Puzzles",
        IAB9_6: "Candle & Soap Making",
        IAB9_7: "Card Games",
        IAB9_8: "Chess",
        IAB9_9: "Cigars",
        IAB9_10: "Collecting",
        IAB9_11: "Comic Books",
        IAB9_12: "Drawing/Sketching",
        IAB9_13: "Freelance Writing",
        IAB9_14: "Genealogy",
        IAB9_15: "Getting Published",
        IAB9_16: "Guitar",
        IAB9_17: "Home Recording",
        IAB9_18: "Investors & Patents",
        IAB9_19: "Jewelry Making",
        IAB9_20: "Magic & Illusion",
        IAB9_21: "Needlework",
        IAB9_22: "Painting",
        IAB9_23: "Photography",
        IAB9_24: "Radio",
        IAB9_25: "Roleplaying Games",
        IAB9_26: "Sci-Fi & Fantasy",
        IAB9_27: "Scrapbooking",
        IAB9_28: "Screenwriting",
        IAB9_29: "Stamps & Coins",
        IAB9_30: "Video & Computer Games",
        IAB9_31: "Woodworking",
        IAB10: "Home & Garden",
        IAB10_1: "Appliances",
        IAB10_2: "Entertaining",
        IAB10_3: "Environmental Safety",
        IAB10_4: "Gardening",
        IAB10_5: "Home Repair",
        IAB10_6: "Home Theater",
        IAB10_7: "Interior Decorating",
        IAB10_8: "Landscaping",
        IAB10_9: "Remodeling & Construction",
        IAB11: "Law, Gov't & Politics",
        IAB11_1: "Immigration",
        IAB11_2: "Legal Issues",
        IAB11_3: "U.S. Government Resources",
        IAB11_4: "Politics",
        IAB11_5: "Commentary",
        IAB12: "News",
        IAB12_1: "International News",
        IAB12_2: "National News",
        IAB12_3: "Local News",
        IAB13: "Personal Finance",
        IAB13_1: "Beginning Investing",
        IAB13_2: "Credit/Debt & Loans",
        IAB13_3: "Financial News",
        IAB13_4: "Financial Planning",
        IAB13_5: "Hedge Fund",
        IAB13_6: "Insurance",
        IAB13_7: "Investing",
        IAB13_8: "Mutual Funds",
        IAB13_9: "Options",
        IAB13_10: "Retirement Planning",
        IAB13_11: "Stocks",
        IAB13_12: "Tax Planning",
        IAB14: "Society",
        IAB14_1: "Dating",
        IAB14_2: "Divorce Support",
        IAB14_3: "Gay Life",
        IAB14_4: "Marriage",
        IAB14_5: "Senior Living",
        IAB14_6: "Teens",
        IAB14_7: "Weddings",
        IAB14_8: "Ethnic Specific",
        IAB15: "Science",
        IAB15_1: "Astrology",
        IAB15_2: "Biology",
        IAB15_3: "Chemistry",
        IAB15_4: "Geology",
        IAB15_5: "Paranormal Phenomena",
        IAB15_6: "Physics",
        IAB15_7: "Space/Astronomy",
        IAB15_8: "Geography",
        IAB15_9: "Botany",
        IAB15_10: "Weather",
        IAB16: "Pets",
        IAB16_1: "Aquariums",
        IAB16_2: "Birds",
        IAB16_3: "Cats",
        IAB16_4: "Dogs",
        IAB16_5: "Large Animals",
        IAB16_6: "Reptiles",
        IAB16_7: "Veterinary Medicine",
        IAB17: "Sports",
        IAB17_1: "Auto Racing",
        IAB17_2: "Baseball",
        IAB17_3: "Bicycling",
        IAB17_4: "Bodybuilding",
        IAB17_5: "Boxing",
        IAB17_6: "Canoeing/Kayaking",
        IAB17_7: "Cheerleading",
        IAB17_8: "Climbing",
        IAB17_9: "Cricket",
        IAB17_10: "Figure Skating",
        IAB17_11: "Fly Fishing",
        IAB17_12: "Football",
        IAB17_13: "Freshwater Fishing",
        IAB17_14: "Game & Fish",
        IAB17_15: "Golf",
        IAB17_16: "Horse Racing",
        IAB17_17: "Horses",
        IAB17_18: "Hunting/Shooting",
        IAB17_19: "Inline Skating",
        IAB17_20: "Martial Arts",
        IAB17_21: "Mountain Biking",
        IAB17_22: "NASCAR Racing",
        IAB17_23: "Olympics",
        IAB17_24: "Paintball",
        IAB17_25: "Power & Motorcycles",
        IAB17_26: "Pro Basketball",
        IAB17_27: "Pro Ice Hockey",
        IAB17_28: "Rodeo",
        IAB17_29: "Rugby",
        IAB17_30: "Running/Jogging",
        IAB17_31: "Sailing",
        IAB17_32: "Saltwater Fishing",
        IAB17_33: "Scuba Diving",
        IAB17_34: "Skateboarding",
        IAB17_35: "Skiing",
        IAB17_36: "Snowboarding",
        IAB17_37: "Surfing/Bodyboarding",
        IAB17_38: "Swimming",
        IAB17_39: "Table Tennis/Ping-Pong",
        IAB17_40: "Tennis",
        IAB17_41: "Volleyball",
        IAB17_42: "Walking",
        IAB17_43: "Waterski/Wakeboard",
        IAB17_44: "World Soccer",
        IAB18: "Style & Fashion",
        IAB18_1: "Beauty",
        IAB18_2: "Body Art",
        IAB18_3: "Fashion",
        IAB18_4: "Jewelry",
        IAB18_5: "Clothing",
        IAB18_6: "Accessories",
        IAB19: "Technology & Computing",
        IAB19_1: "3-D Graphics",
        IAB19_2: "Animation",
        IAB19_3: "Antivirus Software",
        IAB19_4: "C/C++",
        IAB19_5: "Cameras & Camcorders",
        IAB19_6: "Cell Phones",
        IAB19_7: "Computer Certification",
        IAB19_8: "Computer Networking",
        IAB19_9: "Computer Peripherals",
        IAB19_10: "Computer Reviews",
        IAB19_11: "Data Centers",
        IAB19_12: "Databases",
        IAB19_13: "Desktop Publishing",
        IAB19_14: "Desktop Video",
        IAB19_15: "Email",
        IAB19_16: "Graphics Software",
        IAB19_17: "Home Video/DVD",
        IAB19_18: "Internet Technology",
        IAB19_19: "Java",
        IAB19_20: "JavaScript",
        IAB19_21: "Mac Support",
        IAB19_22: "MP3/MIDI",
        IAB19_23: "Net Conferencing",
        IAB19_24: "Net for Beginners",
        IAB19_25: "Network Security",
        IAB19_26: "Palmtops/PDAs",
        IAB19_27: "PC Support",
        IAB19_28: "Portable",
        IAB19_29: "Entertainment",
        IAB19_30: "Shareware/Freeware",
        IAB19_31: "Unix",
        IAB19_32: "Visual Basic",
        IAB19_33: "Web Clip Art",
        IAB19_34: "Web Design/HTML",
        IAB19_35: "Web Search",
        IAB19_36: "Windows",
        IAB20: "Travel",
        IAB20_1: "Adventure Travel",
        IAB20_2: "Africa",
        IAB20_3: "Air Travel",
        IAB20_4: "Australia & New Zealand",
        IAB20_5: "Bed & Breakfasts",
        IAB20_6: "Budget Travel",
        IAB20_7: "Business Travel",
        IAB20_8: "By US Locale",
        IAB20_9: "Camping",
        IAB20_10: "Canada",
        IAB20_11: "Caribbean",
        IAB20_12: "Cruises",
        IAB20_13: "Eastern Europe",
        IAB20_14: "Europe",
        IAB20_15: "France",
        IAB20_16: "Greece",
        IAB20_17: "Honeymoons/Getaways",
        IAB20_18: "Hotels",
        IAB20_19: "Italy",
        IAB20_20: "Japan",
        IAB20_21: "Mexico & Central America",
        IAB20_22: "National Parks",
        IAB20_23: "South America",
        IAB20_24: "Spas",
        IAB20_25: "Theme Parks",
        IAB20_26: "Traveling with Kids",
        IAB20_27: "United Kingdom",
        IAB21: "Real Estate",
        IAB21_1: "Apartments",
        IAB21_2: "Architects",
        IAB21_3: "Buying/Selling Homes",
        IAB22: "Shopping",
        IAB22_1: "Contests & Freebies",
        IAB22_2: "Couponing",
        IAB22_3: "Comparison",
        IAB22_4: "Engines",
        IAB23: "Religion & Spirituality",
        IAB23_1: "Alternative Religions",
        IAB23_2: "Atheism/Agnosticism",
        IAB23_3: "Buddhism",
        IAB23_4: "Catholicism",
        IAB23_5: "Christianity",
        IAB23_6: "Hinduism",
        IAB23_7: "Islam",
        IAB23_8: "Judaism",
        IAB23_9: "Latter-Day Saints",
        IAB23_10: "Pagan/Wiccan",
        IAB24: "Uncategorized",
        IAB25: "Non-Standard Content",
        IAB25_1: "Unmoderated UGC",
        IAB25_2: "Extreme Graphic/Explicit Violence",
        IAB25_3: "Pornography",
        IAB25_4: "Profane Content",
        IAB25_5: "Hate Content",
        IAB25_6: "Under Construction",
        IAB25_7: "Incentivized",
        IAB26: "Illegal Content",
        IAB26_1: "Illegal Content",
        IAB26_2: "Warez",
        IAB26_3: "Spyware/Malware",
        IAB26_4: "CopyrightInfringement",
    }


class PromotionGoal(ConstantBase):
    BRAND_BUILDING = 1
    TRAFFIC_ACQUISITION = 2
    CONVERSIONS = 3

    _VALUES = {
        BRAND_BUILDING: 'Brand Building',
        TRAFFIC_ACQUISITION: 'Traffic Acquisition',
        CONVERSIONS: 'Conversions'
    }


class CampaignGoal(ConstantBase):
    CPA = 1
    PERCENT_BOUNCE_RATE = 2
    NEW_UNIQUE_VISITORS = 3
    SECONDS_TIME_ON_SITE = 4
    PAGES_PER_SESSION = 5

    _VALUES = {
        CPA: 'CPA',
        PERCENT_BOUNCE_RATE: '% bounce rate',
        NEW_UNIQUE_VISITORS: 'new unique visitors',
        SECONDS_TIME_ON_SITE: 'seconds time on site',
        PAGES_PER_SESSION: 'pages per session'
    }


class SourceAction(ConstantBase):
    CAN_UPDATE_STATE = 1
    CAN_UPDATE_CPC = 2
    CAN_UPDATE_DAILY_BUDGET_AUTOMATIC = 3
    CAN_MANAGE_CONTENT_ADS = 4
    HAS_3RD_PARTY_DASHBOARD = 5
    CAN_MODIFY_START_DATE = 6
    CAN_MODIFY_END_DATE = 7
    CAN_MODIFY_DEVICE_TARGETING = 8
    CAN_MODIFY_TRACKING_CODES = 9
    CAN_MODIFY_AD_GROUP_NAME = 10
    CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC = 11
    UPDATE_TRACKING_CODES_ON_CONTENT_ADS = 12
    CAN_UPDATE_DAILY_BUDGET_MANUAL = 13
    CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL = 14
    CAN_MODIFY_DMA_TARGETING_AUTOMATIC = 15
    CAN_MODIFY_COUNTRY_TARGETING = 16
    CAN_MODIFY_DMA_TARGETING_MANUAL = 17

    _VALUES = {
        CAN_UPDATE_STATE: 'Can update state',
        CAN_UPDATE_CPC: 'Can update CPC',
        CAN_UPDATE_DAILY_BUDGET_AUTOMATIC: 'Can update daily budget automatically',
        CAN_MANAGE_CONTENT_ADS: 'Can manage content ads',
        HAS_3RD_PARTY_DASHBOARD: 'Has 3rd party dashboard',
        CAN_MODIFY_START_DATE: 'Can modify start date',
        CAN_MODIFY_END_DATE: 'Can modify end date',
        CAN_MODIFY_DEVICE_TARGETING: 'Can modify device targeting',
        CAN_MODIFY_DMA_TARGETING_AUTOMATIC: 'Can modify DMA targeting automatically',
        CAN_MODIFY_DMA_TARGETING_MANUAL: 'Can modify DMA targeting manually',
        CAN_MODIFY_COUNTRY_TARGETING: 'Can modify targeting by country',
        CAN_MODIFY_TRACKING_CODES: 'Can modify tracking codes',
        CAN_MODIFY_AD_GROUP_NAME: 'Can modify adgroup name',
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC: 'Can modify ad group IAB category automatically',
        UPDATE_TRACKING_CODES_ON_CONTENT_ADS: 'Update tracking codes on content ads',
        CAN_UPDATE_DAILY_BUDGET_MANUAL: 'Can update daily budget manually',
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL: 'Can modify ad group IAB category manually',
    }


class SourceSubmissionType(ConstantBase):
    DEFAULT = 1
    AD_GROUP = 2
    BATCH = 3

    _VALUES = {
        DEFAULT: 'Default',
        AD_GROUP: 'One submission per ad group',
        BATCH: 'Submit whole batch at once'
    }


class SourceType(ConstantBase):
    ADBLADE = 'adblade'
    GRAVITY = 'gravity'
    NRELATE = 'nrelate'
    OUTBRAIN = 'outbrain'
    YAHOO = 'yahoo'
    ZEMANTA = 'zemanta'
    DISQUS = 'disqus'
    B1 = 'b1'

    _VALUES = {
        ADBLADE: 'AdBlade',
        GRAVITY: 'Gravity',
        NRELATE: 'nRelate',
        OUTBRAIN: 'Outbrain',
        YAHOO: 'Yahoo',
        ZEMANTA: 'Zemanta',
        B1: 'B1'
    }


class ConversionPixelStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2
    NOT_USED = 3

    _VALUES = {
        NOT_USED: 'Not used',
        INACTIVE: 'Inactive',
        ACTIVE: 'Active',
    }


class UploadBatchStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3

    _VALUES = {
        DONE: 'Done',
        FAILED: 'Failed',
        IN_PROGRESS: 'In progress'
    }
