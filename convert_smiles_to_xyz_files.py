import os
import paramiko
from rdkit import Chem
from rdkit.Chem import AllChem

def save_mol_to_xyz(RDKit_molecule, file_directory):
    """
    Converts an RDKit molecule to 3D geometry in .xyz file format and saves it locally.
    :param RDKit_molecule: RDKit mol object.
    :param file_directory: Local file path to save the .xyz file
    :return: Saves the .xyz file to the local file path
    """

    if RDKit_molecule is None:
        print(f"Invalid molecule, skipping file creation.")
        return

    # Generate 3D coordinates
    mol = Chem.AddHs(RDKit_molecule)
    AllChem.EmbedMolecule(mol)
    AllChem.MMFFOptimizeMolecule(mol)

    # Get atom positions
    conf = mol.GetConformer()

    with open(file_directory, 'w') as f:
        # Only write the atom positions, skip the first two lines
        f.write(f"{mol.GetNumAtoms()}\n\n")  # Include number of atoms and a blank line
        for atom in mol.GetAtoms():
            pos = conf.GetAtomPosition(atom.GetIdx())
            f.write(f"{atom.GetSymbol()} {pos.x:.4f} {pos.y:.4f} {pos.z:.4f}\n")

    print(f'Converted SMILES to {file_directory}')

def convert_smiles_to_xyzs(local_file_directory, cluster_file_directory, local_folder_directory,
                                         xyz_file_name, xyz_file_number, sftp):
    """
    Convert SMILES strings from a text file on a local file directory to 3D geometry in .xyz file format on a
    remote directory using RDKit.
    :param local_file_directory: Local file path to text file with smiles strings
    :param cluster_file_directory: Remote directory on the cluster to save the .xyz files
    :param local_folder_directory: Local directory to temporarily save the .xyz files before uploading
    :param xyz_file_name: Desired name of the new xyz file, all xyz files will have this same root name. ex: 'substrate'.
    :param xyz_file_number: Desired number of the new xyz file, the SMILES strings in the text file will start  ex: '10' numbering with this
    :param sftp: SSH private key for authentication
    :return: None, converts the SMILES from the local directory to xyz files on a cluster directory.
    """

    # Ensure the output directory exists on the local machine
    os.makedirs(local_folder_directory, exist_ok=True)

    # Read SMILES strings from the file
    with open(local_file_directory, 'r') as file:
        smiles_strings = file.readlines()

    # Iterate through each SMILES string and convert to XYZ
    for i, smiles in enumerate(smiles_strings):

        # Ensure the remote output directory exists
        try:
            cluster_xyz_file_directory = f'{cluster_file_directory}/{xyz_file_name}_{i+xyz_file_number}'
            print(cluster_xyz_file_directory)

            sftp.mkdir(cluster_xyz_file_directory) # Create a new directory for each molecule

        except IOError:
            print(f"Directory {cluster_file_directory} already exists on the cluster.")

        smiles = smiles.strip()  # Remove any surrounding whitespace and newlines
        RDKit_molecule = Chem.MolFromSmiles(smiles)

        if RDKit_molecule: # Check if the molecule was successfully created
            local_xyz_root_directory_directory = os.path.join(local_folder_directory, f'{xyz_file_name}_{i+xyz_file_number}.xyz')
            save_mol_to_xyz(RDKit_molecule, local_xyz_root_directory_directory) # save to local directory first

            # Upload the file to the cluster
            remote_xyz_root_directory = os.path.join(cluster_file_directory, f'{xyz_file_name}_{i+xyz_file_number}.xyz')

            sftp.put(local_xyz_root_directory_directory, remote_xyz_root_directory)

            print(f"Uploaded {local_xyz_root_directory_directory} to {remote_xyz_root_directory}")
        else:
            print(f"Failed to convert SMILES string: {smiles}")


if __name__ == '__main__':

    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the remote server
    client.connect(hostname, username, pkey=private_key)

    sftp = client.open_sftp()

    # Example usage
    convert_smiles_to_xyzs('data/SMILES.csv', '/insomnia001/depts/tekle_smith/users/MKL/project_2', 'local_xyz_root_directory', 'p2', 11, sftp)
