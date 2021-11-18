import functools
import streamlit as st
import extra_streamlit_components as stx
import datetime

cookie_manager_id = 0

# Retrieve cookie if existing
@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

def parse(value, default):
    if value is None:
        return default
    else:
        return type(default)(value)

"## EPFL informations"

gaspard = st.text_input(label="Gaspard", value=parse(cookie_manager.get("gaspard"), ""))
gaspard = gaspard.strip().lower()


email = st.text_input(label="EPFL email", value=parse(cookie_manager.get("email"), ""))
email = email.strip().lower()
email_prefix = email.split("@")[0]


mlo_fs_group = 11169

"## User ID and group ID"

if not email_prefix:
    "If you don't know your UID and GID, **fill your EPFL email above** and we will provide a direct link to your administrative data page."
else:
    f"Visit https://people.epfl.ch/{email_prefix}/admindata to obtain your UID and GID (unfold the administrative data section)."

left, right = st.columns(2)
gid = left.number_input(label="GID", step=1, value=parse(cookie_manager.get("gid"), 0))
uid = right.number_input(label="UID", step=1, value=parse(cookie_manager.get("uid"), 0))

"*The information that you filled above will be stored in your browser cookies for the next times.*"

# Save cookies
expires_at = datetime.datetime.now() + datetime.timedelta(days=365)
cookie_manager.set("gaspard", gaspard, expires_at=expires_at, key="gaspard")
cookie_manager.set("email", email, expires_at=expires_at, key="email")
cookie_manager.set("uid", uid, expires_at=expires_at, key="uid")
cookie_manager.set("gid", gid, expires_at=expires_at, key="gid")


"## Machine setup"

docker_image = st.selectbox('Select a Docker image', ('ic-registry.epfl.ch/mlo/pagliard-base-v2',))
num_gpu = st.number_input("Number of GPUs", min_value=0, value=1, step=1)
num_gpu = int(num_gpu)

def validate():
    if not gaspard:
        st.error("Please provide a valid Gaspard")
    elif not uid:
        st.error("Please provide a valid UID")
    elif not gid:
        st.error("Please provide a valid GID")
    elif not email_prefix:
        st.error("Please provide a valid email")
    else:
        return True
    return False

if validate():

    """## Launch the machine"""

    yaml_file = f"""
apiVersion: run.ai/v1
kind: RunaiJob
metadata:
name: {gaspard}-interactive
labels:
    priorityClassName: "build" # Interactive Job if present, for Train Job REMOVE this line
    user: {gaspard}
spec:
ports:
    - name: "8888"
    port: 8888
    targetPort: 8888
template:
    metadata:
    labels:
        user: {email_prefix} # User e.g. firstname.lastname
    spec:
    hostIPC: true
    schedulerName: runai-scheduler
    restartPolicy: Never
    securityContext:
        runAsUser: {uid}
        runAsGroup: {gid}
        fsGroup: {mlo_fs_group}
    containers:
    - name: container-name
        image: {docker_image}
        workingDir : /home/{gaspard}
        command: ["/bin/bash"]
        args:
        - "-c"
        - "sleep infinity"
        resources:
        limits:
            nvidia.com/gpu: {num_gpu}
        volumeMounts:
        - mountPath: /mlodata1
            name: mlodata1
    volumes:
        - name: mlodata1
        persistentVolumeClaim:
            claimName: runai-pv-mlodata1
    """
    file_name = "launch.yaml"
    f"Download the content file `{file_name}` (content below)."

    st.download_button("DOWNLOAD", yaml_file, file_name=file_name)

    "Launch the machine:"
    st.code(f"kubectl apply -f {file_name}", "bash")

    "Check the status of the pod with:"
    st.code(f"kubectl get pods", "bash")

    "Enter the pod with:"
    st.code(f"runai bash {gaspard}-interactive", "bash")

    "Inside the pod, install anything you want but beaware that only the things on external volumes, like mlodata1, will be kept. The rest will disappear when the pod is stopped."

    "### Jupyter notebook"

    "Maybe start a jupyter notebook. Access the jupyter notebook on your laptop by doing port forwarding:"
    st.code(f"kubectl port-forward {gaspard}-interactive-0-0 8888:8888", "bash")

    "And open http://localhost:8888 in your browser."

    "## Generated YAML config"
    st.code(yaml_file, language="yaml")
