package com.matthandzel.kms

import android.annotation.SuppressLint
import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    companion object {
        const val REQ_PICK_DIR = 1001
        const val REQ_FILE_CHOOSER = 1002
    }
    private lateinit var webView: WebView
    private lateinit var bridge: WebAppInterface
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.webView)
        bridge = WebAppInterface(this)
        setupWebView()

        // Load built web app from assets/www/index.html
        webView.loadUrl("file:///android_asset/www/index.html")
    }

    private fun setupWebView() {
        val s = webView.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.allowFileAccess = true
        s.allowContentAccess = true
        s.cacheMode = WebSettings.LOAD_NO_CACHE
        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest?) {
                request?.grant(request.resources)
            }
            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                this@MainActivity.filePathCallback = filePathCallback
                val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "image/*"
                }
                startActivityForResult(Intent.createChooser(intent, "Select Image"), REQ_FILE_CHOOSER)
                return true
            }
        }
        webView.webViewClient = object : WebViewClient() {}

        webView.addJavascriptInterface(object {
            @android.webkit.JavascriptInterface
            fun pickVaultDirectory(): String {
                return bridge.pickVaultDirectory()
            }
            @android.webkit.JavascriptInterface
            fun getVaultInfo(): String {
                return bridge.getVaultInfo()
            }
            @android.webkit.JavascriptInterface
            fun saveMarkdownAndMedia(json: String): String {
                return bridge.saveMarkdownAndMedia(json)
            }
        }, "KMS")

        val initScript = """
            (function(){
              if (!window.Capacitor) window.Capacitor = {};
              if (!window.Capacitor.Plugins) window.Capacitor.Plugins = {};
              window.Capacitor.Plugins.KMS = {
                pickVaultDirectory: () => Promise.resolve(JSON.parse(window.KMS.pickVaultDirectory())),
                getVaultInfo: () => Promise.resolve(JSON.parse(window.KMS.getVaultInfo())),
                saveMarkdownAndMedia: (payload) => {
                  const p = typeof payload === 'string' ? payload : JSON.stringify(payload);
                  return Promise.resolve(JSON.parse(window.KMS.saveMarkdownAndMedia(p)));
                }
              };
            })();
        """.trimIndent()
        webView.evaluateJavascript(initScript, null)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQ_PICK_DIR && resultCode == Activity.RESULT_OK) {
            val uri: Uri? = data?.data
            if (uri != null) {
                contentResolver.takePersistableUriPermission(
                    uri, Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                )
                bridge.setVaultTree(uri)
            }
        } else if (requestCode == REQ_FILE_CHOOSER) {
            val callback = filePathCallback
            filePathCallback = null
            if (resultCode == Activity.RESULT_OK && data != null) {
                val resultUri: Uri? = data.data
                if (resultUri != null && callback != null) {
                    callback.onReceiveValue(arrayOf(resultUri))
                } else {
                    callback?.onReceiveValue(emptyArray())
                }
            } else {
                callback?.onReceiveValue(emptyArray())
            }
        }
    }
}
