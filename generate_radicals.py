import os
import paramiko

def split_and_generate_radicals(root_directory, secondary_directory, client):
    """
    takes a goat file containing conformer xyz information, splits into different conformers in different root_directories,
    then generates a radical at each hydrogen of each conformer. limited to 10 conformers for speed.
    :param root_directory: directory of the root_directory where the goat ensemble file exists. ex: '/insomnia001/home/mkl2180/2:18/substrates/'
    :param secondary_directory: directory of the goat ensemble file within the root_directory. ex: 'substrate_1'
    :param client: open SSH session variable.
    :return: conformer count (< 10), also splits the goat ensemble file into different conformers then splits those conformers into radicals.
    """

    sftp = client.open_sftp()

    xyz_file_dir = f'{root_directory}/{secondary_directory}/goat.finalensemble.xyz'
    cluster_file_dir = f'{root_directory}/{secondary_directory}/conformers/'

    try:
        # Open the .xyz file on the remote cluster
        with sftp.open(xyz_file_dir, 'r') as file:
            lines = file.readlines()

    except IOError:
        print(f"Failed to open {xyz_file_dir}, skipping.")
        return

    conformer_count = 0
    i = 0

    try:
        sftp.mkdir(cluster_file_dir)

    except IOError:
        print(f"Directory f'{cluster_file_dir}' already exists on the cluster.")

    while i < len(lines):
        try:
            # Ensure the remote output directory exists
            try:
                sftp.mkdir(f'{cluster_file_dir}/conformer_{conformer_count + 1}')
            except IOError:
                print(
                    f"Directory f'{cluster_file_dir}/conformer_{conformer_count + 1}' already exists on the cluster.")

            # Read the number of atoms (first line of the block)
            num_atoms = int(lines[i].strip())  # Convert to int to use in slicing
            num_atoms_str = f"{num_atoms}\n"  # Add newline to match the .xyz format

            # Read the comment line (second line)
            comment_line = lines[i + 1].strip() + '\n'

            # Read the coordinates block (from the third line up to num_atoms lines)
            coordinates_block = ''.join(lines[i + 2:i + 2 + num_atoms])

            # Combine the blocks into one string
            molecule_block = num_atoms_str + comment_line + coordinates_block

            # Save each block as a separate .xyz file on the remote cluster
            output_filename = os.path.join(f'{cluster_file_dir}/conformer_{conformer_count + 1}',
                                           f"conformer_{conformer_count + 1}.xyz")

            with sftp.open(output_filename, 'w') as output_file:
                output_file.write(molecule_block)

            # Move to the next block of lines (num_atoms lines + 2 lines for num_atoms and comment)
            i += num_atoms + 2
            conformer_count += 1

        except Exception as e:
            print(f"Error processing molecule block starting at line {i}: {e}")
            break


    print(f"Processed {conformer_count} molecules from {xyz_file_dir}") # now the conformers have been split into respective root_directorys

    if conformer_count > 10:
        conformer_count = 10  # limit to first 10 conformers for speed

    for conformer in range(1, conformer_count+1):
        print(f"Generating radicals for conformer {conformer}...")

        def save_as_xyz(content, remote_file_path, sftp):
            # Save the modified content directly to the cluster
            with sftp.open(remote_file_path, 'w') as f:
                f.write(content)
            print(f"Saved radical to {remote_file_path}")

        xyz_file_dir = f'{root_directory}/conformers/conformer_{conformer}/conformer_{conformer}.xyz'
        conformer_root_directory_dir = f'{root_directory}/conformers/conformer_{conformer}'

        # Ensure the remote output directory exists
        try:
            sftp.mkdir(conformer_root_directory_dir)
        except IOError:
            print(f"Directory {conformer_root_directory_dir} already exists on the cluster.")

            try:
                with sftp.open(xyz_file_dir, 'r') as file:
                    lines = file.readlines()
            except IOError:
                print(f"Failed to open {xyz_file_dir}, skipping.")

            # Step 2: Modify the first line
            first_line_number = int(lines[0].strip())  # Convert first line to an integer
            lines[0] = f"{first_line_number - 1}\n"  # Add 1 to the number and replace the first line

            # Find the indices of lines that start with 'H'
            hydrogen_indices = [i for i, line in enumerate(lines) if
                                line.strip().startswith('H')]  # can be replaced to generate radicals on any atom

            for i, h_index in enumerate(hydrogen_indices):
                # Create a copy of the lines and remove the hydrogen atom
                file_copy = lines[:]
                del file_copy[h_index]

                # Save the modified content as a new .xyz file directly on the cluster
                remote_output_file_path = os.path.join(conformer_root_directory_dir, f'{h_index - 1}H.xyz')
                save_as_xyz("".join(file_copy), remote_output_file_path, sftp)

    return conformer_count


if __name__ == '__main__':

    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the remote server
    client.connect(hostname, username, pkey=private_key)

    # Example usage
    split_and_generate_radicals(f'/insomnia001/depts/tekle_smith/users/MKL/project_1/', 'substrate_1', client)
