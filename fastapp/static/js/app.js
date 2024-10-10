// header
const header_profile = document.querySelector(".header_profile");
const header_logout = document.querySelector(".header_logout");
const header_register = document.querySelector(".header_register");
const header_login = document.querySelector(".header_login");

// login
const login_modal = document.querySelector("#loginModal");
login_bootstrap_modal = new bootstrap.Modal(login_modal);
const login_form_div = document.querySelector(".login_form");
const register_modal = document.querySelector("#registerModal");

// register
register_bootstrap_modal = new bootstrap.Modal(register_modal);
const register_form_div = document.querySelector(".register_form");
const register_modal_button = document.querySelector(".register_modal_button");
const verify_modal_button = document.querySelector(".verify_modal_button");

// location
const current_location = location.href;
const current_location_auth_api = current_location + "api/auth/v1/";

async function update_access_token() {

} 

function get_local_storage_item(key) {
    item = JSON.parse(localStorage.getItem(key));

    if (!item) {
        return null;
    }

    if (new Date(item.expire) < new Date()) {
        localStorage.removeItem(key);
        return null
    }

    return item.value;
}

function set_local_storage_item(key, value, expire) {
    item = {
        value: value,
        expire: expire
    }
    localStorage.setItem(key, JSON.stringify(item));
}

function check_log_status() {
    access_token = get_local_storage_item("access_token");

    if (access_token) {
        header_register.style.display = "none";
        header_login.style.display = "none";
        header_profile.style.display = "block";
        header_logout.style.display = "block";
    } else {
        header_profile.style.display = "none";
        header_logout.style.display = "none";
        header_register.style.display = "block";
        header_login.style.display = "block";
    }

}

async function user_profile() {
    access_token = get_local_storage_item("access_token");
    if (access_token) {
        url = current_location_auth_api + "user"
        res = await fetch(url, {
            "headers": {
                "accept": "application/json",
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "authorization": "Bearer " + access_token
            },
            "method": "GET",
        });
    }
}

async function user_logout() {
    localStorage.removeItem("access_token");
    url = current_location + "logout"
    await fetch(url, {
        "headers": {
            'accept': 'application/json',
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        "method": "GET",
    });
    check_log_status();
}

async function user_login() {
    let email = login_form_div.querySelector(".email_input").value;
    let password = login_form_div.querySelector(".password_input").value;

    url = current_location_auth_api + "login"

    data = {
        email: email,
        password: password,
    }

    res = await fetch(url, {
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
        method: "POST",
    });

    data = await res.json();

    if (res.status == 200) {
        access_token_info = data;
        set_local_storage_item("access_token", access_token_info["token"], access_token_info["expire"]);

        login_bootstrap_modal.hide();
        check_log_status();
    } else {
        alert(data["detail"]);
    }
}

async function user_register() {
    let email = register_form_div.querySelector(".email_input").value;
    let password = register_form_div.querySelector(".password_input").value;

    url = current_location_auth_api + "register"

    data = {
        email: email,
        password: password,
    }

    res = await fetch(url, {
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
        method: "POST",
    });

    data = await res.json();

    console.log(data)
    if (res.status == 200) {
        register_modal_button.style.display = "none";
        verify_modal_button.style.display = "block";
        document.querySelector(".code_email_input").removeAttribute("readonly");
    } else {
        alert(data["detail"]);
    }
}

async function user_verify() {
    let email = register_form_div.querySelector(".email_input").value;
    let code = register_form_div.querySelector(".code_email_input").value;

    url = current_location_auth_api + "verify"

    data = {
        email: email,
        code: code,
    }

    res = await fetch(url, {
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
        method: "POST",
    });

    data = await res.json();

    console.log(data)
    if (res.status == 200) {
        register_bootstrap_modal.hide();
        login_bootstrap_modal.show();
    } else {
        alert(data["detail"]);
    }
}

function user_login_form() {
    login_bootstrap_modal.show();
}

function user_register_form() {
    register_bootstrap_modal.show();
}


check_log_status();
