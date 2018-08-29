/**
 * The following function is used to convert constants to its property names.
 * This comes in handy when dealing with the new REST api endpoints
 * that convert eg. 1 to "ACTIVE".
 */
export function convertToName(value: any, constantsObj: any) {
    for (const prop in constantsObj) {
        if (constantsObj.hasOwnProperty(prop) && constantsObj[prop] === value) {
            return prop;
        }
    }
}

/**
 * The following function is used to convert names to its constant values.
 * This comes in handy when dealing with the new REST api endpoints
 * that convert eg. "ACTIVE" to 1.
 */
export function convertFromName(value: any, constantsObj: any) {
    return constantsObj[value];
}

/**
 * The following function is used for converting options lists values into
 * REST API flavoured constant values. This comes in handy when dealing
 * with the new REST api endpoints.
 */
export function convertToRestApiCompliantOptions(
    optionsList: any,
    constantsObj: any
) {
    const reversedConstants = {};
    Object.keys(constantsObj).forEach(prop => {
        reversedConstants[constantsObj[prop]] = prop;
    });
    const optionsListNames = optionsList.map((option: any) => {
        const newOption = {...option};
        newOption.value = reversedConstants[option.value];
        return newOption;
    });
    return optionsListNames;
}
