// when making a production release this variable should contain the production number (from the git tag)
variable "PRODUCTION_NUM" {
    default=""
}

// set the Python version, that should be used for the base image
// it MUST be in the format <major>.<minor>
variable "PYTHON_VERSION" {
    default=""
}


// helper function to set the right Docker tag
function "docker_tag" {
    params = [tag]
    result = "iguanaproject/iguana:${tag}"
}


// the default group for building on a normal push or pull request
group "default" {
    targets = [
        "t_development",
        "t_staging",
        "t_staging-nginx"
    ]
}

// this group should be built only on a release push
group "production" {
    targets = [
        "t_production",
        "t_production-nginx"
    ]
}


// TARGET definitions
target "t_base" {
    context = "."
    dockerfile = "Dockerfile"
    args = {
        BASE_IMAGE = notequal("",PYTHON_VERSION) ? "python:${PYTHON_VERSION}-alpine": "python:alpine",
    }
}

target "t_development" {
    inherits = ["t_base"]
    tags = [docker_tag("develop")]
    args = {
        VARIANT = "development",
        USE_NGINX = "false"
    }
}

target "t_staging" {
    inherits = ["t_base"]
    tags = [docker_tag("stage")]
    args = {
        VARIANT = "staging",
        USE_NGINX = "false"
    }
}

target "t_staging-nginx" {
    inherits = ["t_staging"]
    tags = [docker_tag("stage_nginx")]
    args = {
        USE_NGINX = "true"
    }
}

target "t_production" {
    inherits = ["t_base"]
    tags = [
        docker_tag("prod"),
        notequal("",PRODUCTION_NUM) ? docker_tag("prod-${PRODUCTION_NUM}"): ""
    ]
    args = {
        VARIANT = "production"
        USE_NGINX = "false"
    }
}

target "t_production-nginx" {
    inherits = ["t_production"]
    tags = [
        docker_tag("prod_nginx"),
        notequal("",PRODUCTION_NUM) ? docker_tag("prod_nginx-${PRODUCTION_NUM}"): ""
    ]
    args = {
        USE_NGINX = "true"
    }
}
