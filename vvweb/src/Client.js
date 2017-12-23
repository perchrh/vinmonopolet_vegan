// Based on https://github.com/fullstackreact/food-lookup-demo
/* eslint-disable no-undef */
function search(query, cb) {
    // for now implement no search
    return fetch("https://raw.githubusercontent.com/perchrh/vinmonopolet_vegan/master/wine.json", {
        accept: "application/json"
    })
        .then(checkStatus)
        .then(parseJSON)
        .then(cb);
}

function checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
        return response;
    }
    const error = new Error(`HTTP Error ${response.statusText}`);
    error.status = response.statusText;
    error.response = response;
    console.log(error); // eslint-disable-line no-console
    throw error;
}

function parseJSON(response) {
    return response.json();
}

const Client = { search: search };
export default Client;