# Send the corrected video from GitHub Codespaces

This setup combines the corrected video into one MP4, uploads it to your Google Drive, checks the uploaded file, and shares it as **Viewer** with **chriscoyouthaflame2025@gmail.com**. Google Drive is asked to send the recipient a notification. The file remains in your Drive and appears under **Shared with me** for the recipient; it is not copied into their own Drive.

A computer and a Google account are needed. Creating and running a Codespace can use billable GitHub resources. The repository and video are large, so allow time and disk space. Stop the Codespace when finished.

## 1. Create a Codespace on the correct branch

Open the repository's [`arena/5f42c165-videos` branch](https://github.com/wambetebenjamin/Videos/tree/arena/5f42c165-videos). Click **Code → Codespaces → Create codespace on arena/5f42c165-videos**. Wait until it opens, then open its terminal. Creating the Codespace may take time because the video pieces are large.

## 2. Install and sign in to rclone

In the Codespace terminal, run:

```bash
sudo apt-get update && sudo apt-get install -y rclone
rclone config
```

In the interactive configuration:

- Create a new remote named **gdrive** and choose **Google Drive** as the storage type.
- Leave client ID, client secret, root folder ID and service account file blank unless you already have your own. Choose full Drive access, which is needed to upload and share the video.
- For advanced configuration, choose **No**. Since a Codespace is a remote machine, choose **No** when asked whether to use a web browser automatically. Follow rclone's on-screen instructions for authorizing from your own computer's browser. You may need to install rclone on your computer too: https://rclone.org/downloads/.
- Finish and save the **gdrive** remote.

Sign in only to your own Google account and follow the prompts in your terminals. **Never send your rclone configuration, authorization details, or credentials in a chat or commit them to GitHub.** rclone keeps its configuration in the Codespace user's home directory, outside the repository. The uploader reads the access token privately from that configuration and sends it only to Google's Drive API to share the file; it does not print the token.

## 3. Upload and share

In the Codespace terminal, from the repository root, run:

```bash
python3 rest-in-his-presence/revised/codespaces/upload_to_drive.py
```

Keep the Codespace open. The script checks each video piece and the combined video, uploads it to a folder named **Abbas Table - Chrisco Youth** in your Drive, verifies the upload, and shares the verified file with the recipient above. It prints the Drive file link after sharing succeeds. It won't overwrite a different existing file with the same name.

If the upload or sharing fails, the terminal will report that it did not complete. You may rerun the command; it checks the local video and existing upload before sharing. If verification or automatic sharing fails, the file may already be in your Drive: you can open that folder and share the file manually with the email above. Do not share the entire folder publicly.

When finished, stop the Codespace in GitHub to avoid unnecessary usage. Delete it when no longer needed to remove the locally stored rclone configuration and temporary video.
