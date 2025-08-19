package com.matthandzel.kms

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Base64
import android.webkit.JavascriptInterface
import android.webkit.MimeTypeMap
import androidx.documentfile.provider.DocumentFile

class WebAppInterface(private val activity: Activity) {
    companion object {
        private const val PREFS_NAME = "kms_prefs"
        private const val KEY_VAULT_URI = "vault_tree_uri"
    }

    private var vaultTreeUri: Uri? = null
    private var captureDirRel = "capture/raw_capture"
    private var mediaDirRel = "capture/raw_capture/media"

    init {
        val prefs = activity.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val uriStr = prefs.getString(KEY_VAULT_URI, null)
        if (uriStr != null) {
            try {
                vaultTreeUri = Uri.parse(uriStr)
            } catch (_: Exception) {
            }
        }
    }

    @JavascriptInterface
    fun pickVaultDirectory(): String {
        try {
            activity.runOnUiThread {
                val intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).apply {
                    addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or
                             Intent.FLAG_GRANT_READ_URI_PERMISSION or
                             Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                }
                activity.startActivityForResult(intent, MainActivity.REQ_PICK_DIR)
            }
            return "{\"ok\": true}"
        } catch (e: ActivityNotFoundException) {
            return "{\"ok\": false, \"error\": \"${e.message}\"}"
        }
    }

    fun setVaultTree(uri: Uri) {
        vaultTreeUri = uri
        val prefs = activity.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_VAULT_URI, uri.toString()).apply()
    }

    @JavascriptInterface
    fun getVaultInfo(): String {
        val ok = vaultTreeUri != null
        if (!ok) return "{}"
        return "{\"captureDirAbs\":\"$captureDirRel\",\"mediaDirAbs\":\"$mediaDirRel\"}"
    }

    @JavascriptInterface
    fun saveMarkdownAndMedia(jsonPayload: String): String {
        try {
            val payload = org.json.JSONObject(jsonPayload)
            val filename = payload.getString("filename")
            val content = payload.getString("content")
            val media = payload.optJSONArray("media")

            val tree = vaultTreeUri ?: return "{\"ok\":false,\"error\":\"no_vault\"}"
            val treeDoc = DocumentFile.fromTreeUri(activity, tree) ?: return "{\"ok\":false}"
            val captureDir = ensureDir(treeDoc, captureDirRel)
            val mediaDir = ensureDir(treeDoc, mediaDirRel)

            writeTextFile(captureDir, filename, content)

            if (media != null) {
                for (i in 0 until media.length()) {
                    val m = media.getJSONObject(i)
                    val name = m.getString("name")
                    val dataBase64 = m.getString("dataBase64")
                    val type = m.optString("type", null)
                    writeBinaryFile(mediaDir, name, dataBase64, type)
                }
            }

            return "{\"ok\": true}"
        } catch (e: Exception) {
            return "{\"ok\": false, \"error\": \"${e.message}\"}"
        }
    }

    private fun ensureDir(root: DocumentFile, rel: String): DocumentFile {
        var current = root
        val parts = rel.split("/").filter { it.isNotEmpty() }
        for (p in parts) {
            val next = current.findFile(p) ?: current.createDirectory(p)
            current = next!!
        }
        return current
    }

    private fun writeTextFile(dir: DocumentFile, name: String, content: String) {
        val existing = dir.findFile(name)
        if (existing != null && existing.isFile) {
            existing.delete()
        }
        val file = dir.createFile("text/markdown", name)!!
        val os = activity.contentResolver.openOutputStream(file.uri, "w")!!
        os.writer(Charsets.UTF_8).use { it.write(content) }
        os.flush()
        os.close()
    }

    private fun writeBinaryFile(dir: DocumentFile, name: String, base64Data: String, type: String?) {
        val existing = dir.findFile(name)
        if (existing != null && existing.isFile) {
            existing.delete()
        }
        val mime = type ?: guessMime(name)
        val file = dir.createFile(mime, name)!!
        val os = activity.contentResolver.openOutputStream(file.uri, "w")!!
        val bytes = Base64.decode(base64Data, Base64.DEFAULT)
        os.write(bytes)
        os.flush()
        os.close()
    }

    private fun guessMime(name: String): String {
        val ext = name.substringAfterLast('.', "")
        val mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext.lowercase())
        return mime ?: "application/octet-stream"
    }
}
