const collection_checkboxes = document.querySelector(".collection_options");
const collection_div = document.querySelector(".collection_div");
const collection_checkbox_input = document.querySelector(".collection_checkbox_input");

const products_info_div = document.querySelector(".products_info");
const product_div = document.querySelector(".product_div");
const product_combination_div = document.querySelector(".product_combination_div");
const product_collection_div = document.querySelector(".product_collection_div");
const products_search_div = document.querySelector(".products_search_div");
const products_list_div = document.querySelector(".products_list_div");

const search_products_input = document.querySelector(".search_products_input");

let product_page = 0;
let product_page_size = 10;
let last_products_length = 0;
let search_text = ""
let last_get_products_by_scroll_time = 0;


function get_current_time_in_ms() {
    now = new Date();
    return now.getTime();
}


window.onload = (event) => {
    update_collections_boxes();
    update_products_list();
};


function get_selected_collections() {
    collections_checkbox_input = document.querySelectorAll(".collection_checkbox_input");

    collection_ids = [];
    collections_checkbox_input.forEach(collection_input => {
        if (collection_input.checked) {
            collection_ids.push(collection_input.getAttribute("id"));
        }
    });

    return collection_ids;
}


async function get_collections() {
    collections_list = [];
    url = current_location + "api/v1/collection";
    res = await fetch(url, {
        "headers": {
            'accept': 'application/json',
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        "method": "GET",
    });

    collection_list = await res.json();

    return collection_list
}

function validate_collections(collections_list) {
    collection_checkboxes.replaceChildren();

    collections_list.forEach(collection => {
        collection_element = collection_div.cloneNode(true);

        collection_element.style.display = "block";

        collection_input = collection_element.querySelector("input");
        collection_input.setAttribute("id", collection["vsrap_id"]);

        collection_label = collection_element.querySelector("label");
        collection_label.setAttribute("for", collection["vsrap_id"]);
        collection_label.innerHTML = collection["title"];

        collection_checkboxes.appendChild(collection_element);
    });
}

async function update_collections_boxes() {
    collection_list = await get_collections();
    validate_collections(collection_list);
}

async function get_products(search_text, collection_ids) {
    products_list = []
    url = current_location + "api/v1/product?";

    collection_ids.forEach(collection_id => {
        url += "collection_vsrap_ids=" + collection_id + "&";
    });

    url += "page=" + product_page + "&page_size=" + product_page_size;

    if (search_text) {
        url += "&search_text=" + search_text;
    }

    res = await fetch(url, {
        "headers": {
            'accept': 'application/json',
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        "method": "GET",
    })

    products_list = await res.json()

    return products_list
}


function validate_products(products_list) {
    if (product_page == 0) {
        products_list_div.replaceChildren();
    }
    products_list.forEach(product_info => {
        product_element = product_div.cloneNode(true);

        product_element.style.display = "block";
        product_element.querySelector(".product_image").src = product_info["image_url"];
        product_element.setAttribute("vsrap_id", product_info["vsrap_id"]);

        product_element.querySelector(".product_title").innerHTML = product_info["title"];
        product_element.querySelector(".product_price_num").innerHTML = product_info["price"];

        if (product_info["preorder"]) {
            product_element.querySelector(".product_is_preorder").style.display = "None";
        }
        if (product_info["limited"]) {
            product_element.querySelector(".product_is_limited").style.display = "None";
        }

        product_combinations = product_element.querySelector(".product_combinations");
        product_info["combinations"].forEach(combination_info => {
            combination_element = product_combination_div.cloneNode();
            combination_element.style.display = "block";
            combination_element.setAttribute("vsrap_id", combination_info["vsrap_id"]);
            combination_element.setAttribute("combination_number", combination_info["combination_number"]);
            combination_element.innerHTML = combination_info["size"];

            product_combinations.appendChild(combination_element);
        });

        if (product_info["combinations"].length == 0) {
            product_combinations.classList.add("removed");
        }
        
        product_collections = product_element.querySelector(".product_collections");
        product_info["collections"].forEach(collection_info => {
            collection_element = product_collection_div.cloneNode();
            collection_element.style.display = "block";
            collection_element.setAttribute("vsrap_id", collection_info["vsrap_id"]);
            collection_element.innerHTML = collection_info["title"];

            product_collections.appendChild(collection_element);
        });

        products_list_div.appendChild(product_element);
    });
}

async function update_products_list() {
    collection_ids = get_selected_collections();
    products_list = await get_products(search_text, collection_ids);
    validate_products(products_list);
    last_products_length = products_list.length;
}

// Event Listeners

search_products_input.addEventListener("input", () => {
    product_page = 0;
    search_text = search_products_input.value;
    update_products_list();
});


collection_checkboxes.addEventListener("click", (event) => {
    if (event.target && event.target.classList.value == collection_checkbox_input.classList.value) {
        update_products_list();
    }
});


products_list_div.addEventListener('scroll', event => {
    const {scrollHeight, scrollTop, clientHeight} = event.target;

    current_time = get_current_time_in_ms();
    
    if (Math.abs(scrollHeight - clientHeight - scrollTop) < 500 && last_products_length > 0 && (current_time - last_get_products_by_scroll_time) > 500) {
        product_page += 1
        update_products_list();
        last_get_products_by_scroll_time = get_current_time_in_ms();
    }
});