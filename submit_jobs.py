import paramiko

def run_sh_file(root_directory, secondary_directory, sh_file, client, dependency_job_id=None):
    """
    Runs a sh file in root_directory/secondary_directory on the cluster, optionally setting a job dependency.
    returns the job ID of the submitted job.

    :param root_directory: root directory to run .sh file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param sh_file: name of the .sh file to be run with extension. ex: 'xtb.sh', 'goat.sh', 'DFT_geom_1H.sh'
    :param client: open SSH session variable.
    :param dependency_job_id: SLURM job ID that this job should depend on (default: None)- runs when that job is finished.
    :return: job_ID of the submitted sh file job.
    """

    remote_script_path = f"{root_directory}/{secondary_directory}"  # Change to your desired path

    print(f'Running {sh_file} in {root_directory}/{secondary_directory}...')

    # Build the SLURM submission command
    if dependency_job_id:
        dependency_flag = f"--dependency=afterok:{dependency_job_id}"
        command = f"cd {remote_script_path} && sbatch {dependency_flag} {sh_file}"
    else:
        command = f"cd {remote_script_path} && sbatch {sh_file}"

    # Execute the command
    stdin, stdout, stderr = client.exec_command(command)

    # Read the output and error
    output = stdout.read().decode()  # Output of the command
    error = stderr.read().decode()  # Any error messages

    # Print the results
    if output:
        print("Command Output:\n", output)
    if error:
        print("Error Output:\n", error)

    # Extract and return the job ID from the output
    if "Submitted batch job" in output:
        job_id = output.strip().split()[-1]
        print(f"Job submitted with ID: {job_id}")
        return job_id
    else:
        print("Failed to submit job.") # Job submission failed
        return None

def create_sh_file(root_directory, secondary_directory, sh_file, run_file, executable, client):
    """
    creates a sh file in the given directory. xyz name is the xyz file that will be used
    for calculations.

    :param root_directory: root directory to put .sh file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param sh_file: name of the .sh file to be run with extension. ex: 'xtb.sh', 'goat.sh', 'DFT_geom_1H.sh'
    :param run_file: name of file to be run with extension. ex: 'DFT_geom_1H.inp'
    :param executable: ex: 'crest', '$ORCA_PATH/orca', 'xtb'
    :param client: open SSH session variable.
    :return: None, saves .sh file with the sh_file name to the root_directory/substrate_name.
    """

    experiment = sh_file.replace('.sh', '')

    job_path = f'{executable}  {root_directory}/{secondary_directory}/{run_file} {'--opt' if executable == 'xtb' else ''} > {experiment}.out'
    remote_script_path = f'{root_directory}/{secondary_directory}/{sh_file}'

    # Define the content of the bash script
    script_content = f"""#!/bin/bash

#SBATCH --account=free  # account name
#SBATCH --job-name={secondary_directory}  # job name
#SBATCH --ntasks-per-node=2  # number of cores requested by ORCA
#SBATCH --cpus-per-task=1   # number of processor cores (i.e. tasks)
#SBATCH --mem-per-cpu=4G   # memory per CPU core
#SBATCH --time=0-05:00   # walltime in D-HH:MM

# INSERT NOTEBOOK AND EXPERIMENTAL NUMBER OF THE CALCULATION
exp_name={secondary_directory}

# LOAD MODULES, INSERT CODE, AND RUN YOUR PROGRAMS HERE
export NBOEXE=/insomnia001/depts/tekle_smith/users/softwares/NBO/nbo7/bin/nbo7.i8.exe
export NBO7KEY=/insomnia001/depts/tekle_smith/users/softwares/NBO/nbo7/nbo7.key

{job_path}
"""

    # Write the script content to a file on the remote server
    sftp = client.open_sftp()

    with sftp.file(remote_script_path, 'w') as remote_file:
        remote_file.write(script_content)

    client.exec_command(f"chmod +x {remote_script_path}")

    return None

def create_goat_inp_file(root_directory, secondary_directory, run_file, xyz_file, client):
    """
    creates .inp file specifically for xtb's goat in root_directory/secondary_directory with the run_file name.

    :param root_directory: root directory to put and run .inp file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param run_file: name of the input file to create with extension. ex: 'DFT_geom_1H.inp'
    :param xyz_file: xyz file name to perform calculation on with extension. ex: 'xtbopt.xyz'
    :param client: open SSH session variable.
    :return: None, saves run_file to root_directory/substrate_name root_directory.
    """

    script_content = f"""! XTB GOAT PAL2

%maxcore 2000

*xyzfile 0 1 {xyz_file}
"""

    try:

        # Define the path for the script on the remote server
        remote_script_path = f"{root_directory}/{secondary_directory}/{run_file}"  # Change to your desired path

        # Write the script content to a file on the remote server
        sftp = client.open_sftp()
        with sftp.file(remote_script_path, 'w') as remote_file:
            remote_file.write(script_content)

        # Make the script executable
        client.exec_command(f"chmod +x {remote_script_path}")

    finally:
        # Close the connections
        client.close()

def create_DFT_inp_file(root_directory, secondary_directory, run_file, xyz_file, charge, multiplicity, geometry, roks, client):
    """
    creates .inp file specifically for orca's DFT in the root_directory/secondary_directory with the run_file name.
    used for geometry and sp calculations.

    :param root_directory: root directory to put and run .inp file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param run_file: name of input file to create with extension. ex: 'DFT_geom_1H.inp'
    :param xyz_file: xyz file name to perform calculation on with extension. ex: 'xtbopt.xyz'
    :param charge: charge of the system. ex: 0 for closed shell, -1 for anion
    :param multiplicity: multiplicity of the system. ex: 1 for closed shell, 2 for radical
    :param geometry: is this a geometry optimization? if so, set to True
    :param roks: is this a ROKS SP calculation? if so, set to True
    :param client: open SSH session variable.
    :return: None, saves .inp file to root_directory/substrate_name with the run_file name.
    """

    if roks:
        roks = 'ROKS'
    else:
        roks = ''

    if geometry:
        script_content = f"""! BP86 DEF2-TZVP D4 RIJCOSX DEF2/J PAL2 OPT freq
    * xyzfile {charge} {multiplicity} {xyz_file}
    """

    else: # add ROKS keyword if single point calculation on radical
        script_content = f"""! {roks} B3LYP ma-DEF2-TZVP defgrid3 def2/J PAL2 RIJCOSX D4 HIRSHFELD 
        * xyzfile {charge} {multiplicity} {xyz_file}
        
        %SCF 
        maxiter 1000
        end
        
        %maxcore 2000
        
        %output
          Print[ P_Basis ] 2
          Print[ P_MOs ] 1
          Print[ P_ReducedOrbPopMO_L] 1
        end
    """

    # Define the path for the script on the remote server
    remote_script_path = f"{root_directory}/{secondary_directory}/{run_file}"  # Change to your desired path
    print(remote_script_path)

    # Write the script content to a file on the remote server
    sftp = client.open_sftp()

    print('path:', remote_script_path)
    with sftp.file(remote_script_path, 'w') as remote_file:
        remote_file.write(script_content)

    # Make the script executable
    client.exec_command(f"chmod +x {remote_script_path}")

def submit_xtb_and_goat_calculations(root_directory, secondary_directory, run_file, client):
    """
    submit xtb optimization and goat conformer search for lower level optimization.
    goat is submitted with a dependency to the xtb job.

    :param root_directory: root directory to put and run .inp file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param run_file: name of input file to create with extension. ex: 'DFT_geom_1H.inp'
    :param client: open SSH session variable.
    :return: None, just submits xtb and goat jobs.
    """

    create_sh_file(root_directory, secondary_directory, 'xtb.sh', run_file, 'xtb', client)
    job_ID = run_sh_file(root_directory, secondary_directory, 'xtb.sh', client)

    print('submitted xtb')

    # run goat file when xtb is done
    create_goat_inp_file(root_directory, secondary_directory, 'goat.inp', 'xtbopt.xyz', client)
    create_sh_file(root_directory, secondary_directory, 'goat.sh', 'goat.inp', '$ORCA_PATH/orca', client)
    run_sh_file(root_directory, secondary_directory, 'goat.sh', client, dependency_job_id=job_ID)

    print('submitted goat with xtb dependency')

    return None

def submit_SOMO_and_electrophilicity_calculations(root_directory, secondary_directory, hydrogen_list, client):
    """
    after submitting xtb and goat jobs, submit DFT-level calculations for the substrate and radicals.
    generate_radicals.py should be run before this to generate the radical xyz files.
    then, geometry optimization for all radical sites of the relevant conformers. SP calculations for SOMO energy as well as anion and cation for electrophilicity calculations are also
    submitted, with dependency to the geometry optimization job.

    :param root_directory: root directory to put and run .inp file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param hydrogen_list: list of hydrogen atomic numbers to submit calculations for. ex: [1, 2, 3]
    :param client: open SSH session variable.
    :return: None, just submits all jobs for somo and philicity calculations.
    """

    conformer_count = 1

    for conformer in range(1, conformer_count+1):

        for hydrogen in hydrogen_list:

            # geometry optimization
            create_DFT_inp_file(root_directory, f'{secondary_directory}/conformers/conformer_{conformer}/', f'DFT_geom_{hydrogen}H.inp', f'{hydrogen}H.xyz', 0, 2, True, False, client)
            create_sh_file(root_directory, f'{secondary_directory}/conformers/conformer_{conformer}/', f'DFT_geom_{hydrogen}H.sh', f'DFT_geom_{hydrogen}H.inp', '$ORCA_PATH/orca', client)

            # single point calculation
            create_DFT_inp_file(root_directory, f'{secondary_directory}/conformers/conformer_{conformer}/',f'DFT_elec_{hydrogen}H.inp', f'DFT_geom_{hydrogen}H.xyz', 0, 2, False, True, client)
            create_sh_file(root_directory, f'{secondary_directory}/conformers/conformer_{conformer}/', f'DFT_elec_{hydrogen}H.sh',f'DFT_elec_{hydrogen}H.inp', '$ORCA_PATH/orca', client)

            job_ID = run_sh_file(root_directory, f'{secondary_directory}/conformers/conformer_{conformer}/', f'DFT_geom_{hydrogen}H.sh', client)
            run_sh_file(root_directory, f'{secondary_directory}/conformers/conformer_{conformer}/', f'DFT_elec_{hydrogen}H.sh', client, job_ID)

    for conformer in range(1, conformer_count+1):

        # define the path for this conformer's Hirshfeld calculations
        hirshfeld_path = f"{root_directory}/{secondary_directory}/hirshfeld/conformer_{conformer}/"

        try:
            # make sure hirshfeld directory exists
            mkdir_command = f'mkdir -p {hirshfeld_path}'
            client.exec_command(mkdir_command)

        except IOError:
            print(
                f"Directory f'{hirshfeld_path}' already exists on the cluster.")

        # use the optimized radical structures for cation/anion calculations
        for hydrogen in hydrogen_list:

            # anion calc
            create_DFT_inp_file(f'{root_directory}', f'/{secondary_directory}/hirshfeld/conformer_{conformer}/', f'DFT_elec_{hydrogen}H_anion.inp',  f'{root_directory}/{secondary_directory}/conformer/conformer_{conformer}/DFT_geom_{hydrogen}H.xyz', -1, 1, False, False, client)
            create_sh_file(root_directory, secondary_directory, f'DFT_elec_{hydrogen}H_anion.sh',f'DFT_elec_{hydrogen}H_anion.inp', '$ORCA_PATH/orca', client)
            run_sh_file(f'{root_directory}', f'/{secondary_directory}/hirshfeld/conformer_{conformer}/', f'DFT_elec_{hydrogen}H_anion.sh', client)

            # cation calc
            create_DFT_inp_file(f'{root_directory}', f'/{secondary_directory}/hirshfeld/conformer_{conformer}/',f'DFT_elec_{hydrogen}H_cation.inp', f'{root_directory}/{secondary_directory}/conformer/conformer_{conformer}/DFT_geom_{hydrogen}H.xyz', 1, 1, False, False, client)
            create_sh_file(root_directory, secondary_directory, f'DFT_elec_{hydrogen}H_cation.sh', f'DFT_elec_{hydrogen}H_cation.inp','$ORCA_PATH/orca', client)
            run_sh_file(f'{root_directory}', f'/{secondary_directory}/hirshfeld/conformer_{conformer}/', f'DFT_elec_{hydrogen}H_cation.sh', client)

    print('submitted SOMO and electrophilicity calculations')


def submit_atomic_charge_calculations(root_directory, secondary_directory, client):
    """
    geometry optimization on the closed shell substrate, then single point calculation.
    NBO charge, Mulliken charge, Hirshfeld charge, and Lowdin charge for each hydrogen is achieved from this calculation.
    creat_e_DFT_inp_file() needs to be changed to include the NBO keyword.

    :param root_directory: root directory to put and run .inp file. ex: '/insomnia001/depts/tekle_smith/users/MKL/ma_def2_TZVP/'
    :param secondary_directory: secondary directory name. ex: 'substrate_1', combines with root_directory to form full path.
    :param client: open SSH session variable.
    :return: None, just submits a geometry optimization and single point calculation for the closed shell substrate.
    """

    # geometry optimization
    create_DFT_inp_file(root_directory,  secondary_directory, f'DFT_geom.inp', 'goat.globalminimum.xyz',0, 1, True, False, client)
    create_sh_file(root_directory, secondary_directory, f'DFT_geom.sh',f'DFT_geom.inp', '$ORCA_PATH/orca', client)

    # single point calculation
    create_DFT_inp_file(root_directory, secondary_directory,'DFT_elec.inp', 'DFT_geom.xyz',  0, 1, False, False, client)
    create_sh_file(root_directory, secondary_directory, f'DFT_elec.sh', f'DFT_elec.inp', '$ORCA_PATH/orca', client)

    job_ID = run_sh_file(root_directory, secondary_directory, f'DFT_geom.sh', client)
    run_sh_file(root_directory, secondary_directory, f'DFT_elec_ma_def2_TZVP.sh', client, job_ID)

    print('submitted NBO charge calculation')

    return None

if __name__ == '__main__':

    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the remote server with passkey
    client.connect(hostname, username, pkey=private_key)

    # Example usage - submit xtb and goat calculations
    submit_xtb_and_goat_calculations(f'/insomnia001/depts/tekle_smith/users/MKL/project_2', f'p2_11', 'p2_11.xyz', client)

    # Example usage - submit SOMO and electrophilicity calculations
    submit_SOMO_and_electrophilicity_calculations(f'/insomnia001/depts/tekle_smith/users/MKL/project_2', f'p2_1', [9, 10], client)