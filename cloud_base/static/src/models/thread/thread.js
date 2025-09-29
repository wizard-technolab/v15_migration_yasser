/** @odoo-module **/

import {
    registerInstancePatchModel,
    registerFieldPatchModel,
} from "@mail/model/model_core";
import { attr, many2many } from "@mail/model/model_field";
import { insertAndReplace, replace } from "@mail/model/model_field_command";


registerInstancePatchModel("mail.thread", "cloud_base/static/src/models/thread/thread.js", {               
    /*
     * Re-write to show our folder-related attachments, but keep OriginThreadAttachments for messages
    */ 
    _computeAllAttachments() {
        const allAttachments = [...new Set(this.folderOriginThreadAttachments.concat(this.attachments))]
            .sort((a1, a2) => {
                // "uploading" before "uploaded" attachments.
                if (!a1.isUploading && a2.isUploading) {
                    return 1;
                }
                if (a1.isUploading && !a2.isUploading) {
                    return -1;
                }
                // "most-recent" before "oldest" attachments.
                return Math.abs(a2.id) - Math.abs(a1.id);
            });
        return replace(allAttachments);
    },
    /*
     * The method to fetch attachments according to the current folder
    */ 
    async fetchAttachmentsFormatted(folder_domain, checked_folder) {
        if (this.isTemporary) {
            return;
        }
        const requestSet = new Set(["attachments"]);
        if (requestSet.has("attachments")) {
            this.update({ isLoadingAttachments: true });
        }
        const {
            attachments: attachmentsData,
        } = await this.env.services.rpc({
            route: "/mail/thread/data",
            params: {
                request_list: [...requestSet],
                thread_id: this.id,
                thread_model: this.model,
                checked_folder: checked_folder,
                folder_domain: folder_domain,
            },
        }, { shadow: true });
        if (!this.exists()) {
            return;
        }
        const values = {};
        if (!checked_folder) {
            // when folder is not checked (so, the first load), we should update origin attachments
            Object.assign(values, {
                originThreadAttachments: insertAndReplace(attachmentsData),
            });
        };
        if (attachmentsData) {
            Object.assign(values, {
                areAttachmentsLoaded: true,
                isLoadingAttachments: false,
                folderOriginThreadAttachments: insertAndReplace(attachmentsData),
            });
        }
        this.update(values);
    },
    /*
      * Fully re-write to fetch also URL and convert data on fly; and then folders
    */
    async fetchAttachments() {
        await this.fetchAttachmentsFormatted(false, false)
        var cloudFolders = await this.async(() => this.env.services.rpc({
            model: "clouds.folder",
            method: "action_js_find_folders_by_res_params",
            args: [this.model, this.id],
        }));
        this.update({ cloudFolders: cloudFolders});
    },
    /*
     * Refresh attachment box when checked folder is chanegd
    */
    async refreshForFolder(folder_domain, checked_folder) {
        if (this.isTemporary) {
            return;
        }
        this.update({ isLoadingAttachments: true });
        await this.async(() => this.fetchAttachmentsFormatted(folder_domain, checked_folder));
        this.update({ isLoadingAttachments: false });
    },
});

registerFieldPatchModel("mail.thread", "cloud_base/static/src/models/thread/thread.js", {
    /*
     * Object defining linked clouds folders
     */
    cloudFolders: attr({ default: [], }),
    folderOriginThreadAttachments: many2many("mail.attachment", { isCausal: false }),
});
