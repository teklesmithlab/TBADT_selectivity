import paramiko

def read_mulliken_and_loewdin_charges(file_directory, atom_number, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the mulliken and loewdin charges for a specified atom.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_elec_substrate_1.out'
    :param atom_number: atomic number to extract charges for. ex: 8
    :param sftp: open SSH session variable
    :return: mulliken, lowdin values for the specified atom.
    """

    atom_number = atom_number - 1 # .out files are zero indexed

    # Open and read the file from the remote directory
    with sftp.open(file_directory, 'r') as file:
        lines = file.readlines()

    # Initialize variables to store charges
    mulliken_charge = None
    lowdin_charge = None

    # Find the Mulliken and Loewdin analysis sections and retrieve charges
    for i in range(len(lines)):
        line = lines[i].strip()

        # Mulliken charges section
        if line.startswith('MULLIKEN ATOMIC CHARGES'):
            for j in range(i + 2, len(lines)):
                if 'Sum of atomic charges' in lines[j]:
                    break
                split_line = lines[j].split(':')
                if len(split_line) == 2:
                    atom_index = int(split_line[0].strip().split()[0])
                    if atom_index == atom_number:
                        mulliken_charge = float(split_line[1].strip())
                        break

        # Loewdin charges section
        if line.startswith('LOEWDIN ATOMIC CHARGES'):
            for j in range(i + 2, len(lines)):
                if 'Sum of atomic charges' in lines[j]:
                    break
                split_line = lines[j].split(':')
                if len(split_line) == 2:
                    atom_index = int(split_line[0].strip().split()[0])
                    if atom_index == atom_number:
                        lowdin_charge = float(split_line[1].strip())
                        break

    # Check if charges were found
    if mulliken_charge is None:
        print(f"Atom {atom_number} not found in Mulliken data.")
    if lowdin_charge is None:
        print(f"Atom {atom_number} not found in Loewdin data.")

    return mulliken_charge, lowdin_charge

def read_hirshfeld_charge(file_directory, atom_number, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the hirshfeld charge for a specified atom.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_elec_substrate_1.out'
    :param atom_number: atomic number to extract charges for. ex: 8
    :param sftp: open SSH session variable.
    :return: hirshfeld values for the specified atom.
    """

    # Open and read the file from the remote directory
    with sftp.open(file_directory, 'r') as file:
        lines = file.readlines()

    # Find the Hirshfeld analysis section
    start = -1
    for i in range(len(lines)):
        if lines[i].strip().startswith('HIRSHFELD ANALYSIS'):
            start = i
            break

    if start == -1:
        print("HIRSHFELD ANALYSIS section not found.")
        return None, None

    # Skip the header and find where the atom data starts
    hirshfeld_data_start = start + 6  # The data starts 6 lines after 'HIRSHFELD ANALYSIS'

    # Locate and extract charges
    for line in lines[hirshfeld_data_start:]:
        split_line = line.split()

        # Skip any non-numeric lines (like header lines)
        if len(split_line) < 4 or not split_line[0].isdigit():
            continue

        # Extract atom index and check if it's the requested atom number
        atom_idx = int(split_line[0])  # Atom index

        # If the atom index matches, extract and return charge and spin
        if atom_idx == atom_number:
            charge = float(split_line[2])  # Hirshfeld charge
            return charge

def read_philicity(folder_directory, atom_number, sftp):
    """
    reads the philicity of a specified hydrogen atom in a folder containing DFT output files for the anion, cation, and radical.
    :param folder_directory: folder containing the DFT output files. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/'
    :param atom_number: atomic number to extract philicity for. ex: 8
    :param sftp: open SSH session variable.
    :return: radical philicity at the specified atom.
    """

    anion_scf = read_scf_energy(f'{folder_directory}/DFT_elec_{atom_number}H_anion.out', sftp)
    cation_scf = read_scf_energy(f'{folder_directory}/DFT_elec_{atom_number}H_cation.out', sftp)
    radical_scf = read_scf_energy(f'{folder_directory}/DFT_elec_{atom_number}H_radical.out', sftp)

    I = cation_scf - radical_scf
    A = radical_scf - anion_scf

    philicity = ((I + A)**2) / (I - A) * (1 / 8) * 27.2  # convert to eV

    return philicity

def read_somo(file_directory, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the somo orbital energy for a specified atom.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_elec_substrate_1.out'
    :param sftp: open SSH session variable.
    :return: SOMO energy at the specified atom.
    """
    orbital_section_found = False

    with sftp.open(file_directory, 'r') as file:
        for line in file:
            if not orbital_section_found:
                if line.strip().startswith('ORBITAL ENERGIES'):
                    orbital_section_found = True
                    # Skip next 3 lines (headers)
                    for _ in range(3):
                        next(file)
                    continue

            elif orbital_section_found:
                parts = line.split()

                # Typical format: [index, occupancy, energy_H, energy_eV]
                if len(parts) >= 4 and parts[1] == '1.0000':
                    try:
                        energy_ev = float(parts[3])  # read directly in eV
                        return energy_ev
                    except ValueError:
                        continue

    print("SOMO orbital not found.")
    return None

def read_thermal_enthalpy_correction(file_directory, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the thermal enthalpy correction for the calculation.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_geom_substrate_1.out'
    :param sftp: open SSH session variable.
    :return: thermal enthalpy correction value.
    """

    with sftp.open(file_directory, 'r') as file:
        for line in file:
            if "Thermal Enthalpy correction" in line:
                # The value is the 5th token on the line (index 4)
                return float(line.split()[4])

def read_scf_energy(file_directory, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the final SCF energy.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_elec_substrate_1.out'
    :param sftp: open SSH session variable.
    :return: scf energy value.
    """
    with sftp.open(file_directory, 'r') as file:
        lines = file.readlines()

    for line in reversed(lines):  # Start from the bottom
        if 'FINAL SINGLE POINT ENERGY' in line:
            return float(line.split()[-1])

    print("SCF energy not found.")
    return None

def read_gibbs_and_electronic_energies(file_directory, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the final Gibbs free energy and electronic energy.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_elec_substrate_1.out'
    :param sftp: open SSH session variable.
    :return: gibbs energy value, electronic energy value.
    """
    with sftp.open(file_directory, 'r') as file:
        lines = file.readlines()

    gibbs_energy = None
    electronic_energy = None

    # Iterate from the bottom to reach the final energies faster
    for i in range(len(lines) - 1, 0, -1):
        line = lines[i]

        if gibbs_energy is None and "Final Gibbs free energy" in line:
            gibbs_energy = float(line.split()[-2])

        if electronic_energy is None and "Electronic energy" in line and "Summary of contributions" in lines[i - 1]:
            electronic_energy = float(line.split()[-2])

        if gibbs_energy is not None and electronic_energy is not None:
            break

    if gibbs_energy is None:
        print("Gibbs energy not found.")
    if electronic_energy is None:
        print("Electronic energy not found.")

    return gibbs_energy, electronic_energy

def read_nbo_charge(file_directory, atom_number, sftp):
    """
    uses sftp to open the specified file on a remote cluster and reads the nbo charge for a specified atom.
    :param file_directory: .out file directory. ex: '/insomnia001/home/mkl2180/2:18/substrates/substrate_1/DFT_elec_substrate_1.out'
    :param atom_number: atomic number to extract charges for. ex: 8
    :param sftp: open SSH session variable.
    :return: nbo charge value for the specified atom.
    """
    with sftp.open(file_directory, 'r') as f:
        lines = f.readlines()

        # Look for the NBO analysis section
        in_nbo_section = False
        for line in lines:
            if "Summary of Natural Population Analysis:" in line:
                in_nbo_section = True
                continue
            if in_nbo_section:
                if line.strip().startswith("==="):  # end of section
                    break
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        atom_label = parts[0]
                        atom_idx = int(parts[1])
                        if atom_label == "H" and atom_idx == atom_number:
                            return float(parts[2])  # Natural charge
                    except ValueError:
                        continue  # skip malformed lines

if __name__ == '__main__':

    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the remote server
    client.connect(hostname, username, pkey=private_key)
    sftp = client.open_sftp()

    # Example usage
    print(read_philicity('/insomnia001/depts/tekle_smith/users/MKL/project_3/p3_3/', 20, sftp))