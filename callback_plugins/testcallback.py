from ansible.plugins.callback import CallbackBase
from ansible.utils.unsafe_proxy import AnsibleUnsafeText
import json

def Inv_Update(inv_name,node_name):
    import os
    import requests
    import yaml

    print (node_name)
    print ("###################")
    # === CONFIGURATION FROM ENVIRONMENT ===
    AAP_URL = os.getenv("TOWER_HOST", "https://controller.example.org")
    USERNAME = os.getenv("TOWER_USERNAME", "admin")
    PASSWORD = os.getenv("TOWER_PASSWORD", "redhat")
    VERIFY_SSL = os.getenv("TOWER_VERIFY_SSL", "false").lower() != "false"
    #INVENTORY_NAME = "Testextrastat"
    INVENTORY_NAME = inv_name

    # === AUTHENTICATE AND GET TOKEN ===
    auth_url = f"{AAP_URL}/api/v2/tokens/"
    auth_response = requests.post(auth_url, auth=(USERNAME, PASSWORD), verify=VERIFY_SSL)
    auth_response.raise_for_status()
    token = auth_response.json()["token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # === STEP 1: Lookup Inventory ID by Name ===
    lookup_url = f"{AAP_URL}/api/v2/inventories/?name={INVENTORY_NAME}"
    lookup_response = requests.get(lookup_url, headers=headers, verify=VERIFY_SSL)
    lookup_response.raise_for_status()

    results = lookup_response.json().get("results", [])
    if not results:
        raise Exception(f"❌ Inventory '{INVENTORY_NAME}' not found.")

    inventory_id = results[0]["id"]
    inventory_url = f"{AAP_URL}/api/v2/inventories/{inventory_id}/"

    print (inventory_url)

    # === STEP 2: Get existing inventory variables ===
    response = requests.get(inventory_url, headers=headers, verify=VERIFY_SSL)
    response.raise_for_status()
    inventory_data = response.json()

    existing_vars = inventory_data.get("variables", "")
    vars_dict = yaml.safe_load(existing_vars) if existing_vars else {}

    # === STEP 3: Append 'task3' to stats array ===
    stats = vars_dict.get("stats", [])
    if not isinstance(stats, list):
        stats = []

    clean_stats = [str(item) for item in stats if item]


    print (stats)
    print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    new_nodename=str(node_name)
    if node_name not in stats:
        clean_stats.append(new_nodename)
        vars_dict["stats"] = clean_stats
        print(f"✅ {node_name} appended to inventory-level stats.")
    else:
        print(f"ℹ️ {node_name} already exists in stats.")

    print (stats)
    print (vars_dict)
    print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    # === STEP 4: Convert back to YAML and update inventory ===

    def sanitize_vars(obj):
        try:
            # Catch known unsafe types by class name
            if hasattr(obj, '__class__'):
                class_name = obj.__class__.__name__
                if class_name.startswith(("AnsibleUnsafe", "NativeJinjaUnsafe", "Jinja", "AnsibleProxy")):
                    return str(obj)
            # Recursively sanitize containers
            if isinstance(obj, dict):
                return {str(sanitize_vars(k)): sanitize_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_vars(i) for i in obj]
            elif isinstance(obj, tuple):
                return tuple(sanitize_vars(i) for i in obj)
            elif isinstance(obj, set):
                return {sanitize_vars(i) for i in obj}
            elif not isinstance(obj, (str, int, float, bool, type(None))):
                return str(obj)
            else:
                return obj
        except Exception as e:
            print(f"❌ Error sanitizing object: {repr(obj)} — {e}")
            return str(obj)

    #cleaned_dict = sanitize_vars(vars_dict)
    cleaned_dict=vars_dict
    print (cleaned_dict)
    import sys
    try:
         updated_vars_yaml = yaml.safe_dump(cleaned_dict, default_flow_style=False)
    except Exception as e:
          print ("insiodeeeeeeeeeeeeeeeeeeeeeeeeeeee")
          updated_vars_yaml = str(cleaned_dict)


    #safe_data = sanitize_vars(stats)

    print (updated_vars_yaml)
    patch_payload = {
        "variables": updated_vars_yaml
    }

    patch_response = requests.patch(inventory_url, headers=headers, json=patch_payload, verify=VERIFY_SSL)
    patch_response.raise_for_status()

    print("✅ Inventory-level variables updated successfully.")

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'my_custom_plugin'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.node_name = None
        self.inv_name = None
        self.skip_callback = None


    def v2_playbook_on_play_start(self, play):
        self.play = play
    def v2_playbook_on_start(self, playbook):
        print("Playbook started!")

    def v2_runner_on_ok(self, result):
        print(f"succeeded on {result._host.get_name()}")
        task_name = result._task.get_name()
        print (task_name)
        if "Set node_name value" in task_name:
            self.node_name = result._result.get('msg', '')

        if "Set inv_name value" in task_name:
            self.inv_name = result._result.get('msg', '')
            print (self.node_name)
            print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        if "Set skip_callback value" in task_name:
            self.skip_callback = result._result.get('msg', '')

    def v2_playbook_on_stats(self, stats):
        # Check if any hosts failed
        run_data = stats.custom.get("_run", {})
        node_name = self.node_name
        inv_name = self.inv_name
        custom_stats = self.skip_callback
        print (custom_stats)
        if custom_stats:
           return

        failed_hosts = stats.failures
        unreachable_hosts = stats.dark
        if failed_hosts or unreachable_hosts:
            print("❌ Playbook failed. Running failure task...")
        else:
            Inv_Update(inv_name,node_name)
            print("✅ Playbook succeeded. Running success task...")
            print (f"{inv_name}")
