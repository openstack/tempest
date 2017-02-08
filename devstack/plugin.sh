if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
    :

elif [[ "$1" == "stack" && "$2" == "install" ]]; then
    :

elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    :

elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
    if is_service_enabled ucsm-tests; then
        # Update nova policy to let non-admin user to run instance on a certain compute host
        # For test_non_sriov_intra_vm_to_vm test
        sudo sed -i 's/compute:create:forced_host": "is_admin:True"/compute:create:forced_host": ""/' /etc/nova/policy.json
    fi
fi

if [[ "$1" == "unstack" ]]; then
    :
fi

if [[ "$1" == "clean" ]]; then
    :
fi