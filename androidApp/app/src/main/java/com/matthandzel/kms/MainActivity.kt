package com.matthandzel.kms

import android.annotation.SuppressLint
import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    companion object {
        const val REQ_PICK_DIR = 1001
    }
    private lateinit var webView: WebView
    private lateinit var bridge: WebAppInterface

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
        webView.webChromeClient = WebChromeClient()
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

        // Provide a small bootstrap to create window.Capacitor-like facade backed by KMS interface
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
        }
    }
}
