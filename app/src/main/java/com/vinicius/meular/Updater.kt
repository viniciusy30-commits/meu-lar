package com.vinicius.meular

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.widget.ProgressBar
import android.widget.Toast
import androidx.core.content.FileProvider
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

object Updater {
    const val REPO = "viniciusy30-commits/meu-lar"

    @Suppress("DEPRECATION")
    private fun versaoAtual(a: Activity): Int =
        a.packageManager.getPackageInfo(a.packageName, 0).versionCode

    fun autoCheck(a: Activity) {
        val p = a.getSharedPreferences("updater", Context.MODE_PRIVATE)
        val agora = System.currentTimeMillis()
        if (agora - p.getLong("ultima", 0L) < 6 * 3600 * 1000L) return
        p.edit().putLong("ultima", agora).apply()
        check(a, false)
    }

    fun check(a: Activity, manual: Boolean) {
        if (manual) Toast.makeText(a, "Procurando atualização...", Toast.LENGTH_SHORT).show()
        Thread {
            try {
                val c = URL("https://api.github.com/repos/$REPO/releases/latest").openConnection() as HttpURLConnection
                c.connectTimeout = 10000; c.readTimeout = 10000
                c.setRequestProperty("Accept", "application/vnd.github+json")
                val j = JSONObject(c.inputStream.bufferedReader().readText())
                val nova = j.getString("tag_name").removePrefix("v").toIntOrNull() ?: 0
                var url: String? = null
                val assets = j.getJSONArray("assets")
                for (k in 0 until assets.length()) {
                    val n = assets.getJSONObject(k)
                    if (n.getString("name").endsWith(".apk")) { url = n.getString("browser_download_url"); break }
                }
                a.runOnUiThread {
                    if (url != null && nova > versaoAtual(a)) dialogoNova(a, nova, url)
                    else if (manual) Toast.makeText(a, "Você já está na versão mais nova.", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                if (manual) a.runOnUiThread {
                    Toast.makeText(a, "Sem internet ou nenhuma versão encontrada.", Toast.LENGTH_LONG).show()
                }
            }
        }.start()
    }

    private fun dialogoNova(a: Activity, v: Int, url: String) {
        AlertDialog.Builder(a)
            .setTitle("Nova versão disponível")
            .setMessage("A versão $v está pronta. Quer atualizar agora?")
            .setPositiveButton("Atualizar") { _, _ -> comecar(a, url) }
            .setNegativeButton("Depois", null)
            .show()
    }

    private fun comecar(a: Activity, url: String) {
        if (Build.VERSION.SDK_INT >= 26 && !a.packageManager.canRequestPackageInstalls()) {
            AlertDialog.Builder(a)
                .setTitle("Permissão necessária")
                .setMessage("Para atualizar, libere \"Instalar apps desconhecidos\" para o Meu Lar na próxima tela e volte ao app.")
                .setPositiveButton("Abrir configuração") { _, _ ->
                    a.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + a.packageName)))
                }
                .setNegativeButton("Cancelar", null)
                .show()
            return
        }
        val barra = ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal)
        barra.max = 100
        val d = AlertDialog.Builder(a).setTitle("Baixando atualização...").setView(barra).setCancelable(false).show()
        Thread {
            try {
                val dir = File(a.cacheDir, "updates"); dir.mkdirs()
                val f = File(dir, "MeuLar.apk")
                val c = URL(url).openConnection() as HttpURLConnection
                c.connectTimeout = 15000; c.readTimeout = 30000
                val total = c.contentLength
                c.inputStream.use { ins ->
                    f.outputStream().use { out ->
                        val buf = ByteArray(16384)
                        var lido = 0L
                        while (true) {
                            val n = ins.read(buf)
                            if (n < 0) break
                            out.write(buf, 0, n); lido += n
                            if (total > 0) a.runOnUiThread { barra.progress = (lido * 100 / total).toInt() }
                        }
                    }
                }
                a.runOnUiThread {
                    d.dismiss()
                    val uri = FileProvider.getUriForFile(a, a.packageName + ".fileprovider", f)
                    val i = Intent(Intent.ACTION_VIEW)
                    i.setDataAndType(uri, "application/vnd.android.package-archive")
                    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
                    a.startActivity(i)
                }
            } catch (e: Exception) {
                a.runOnUiThread {
                    d.dismiss()
                    Toast.makeText(a, "Falha no download. Tente de novo.", Toast.LENGTH_LONG).show()
                }
            }
        }.start()
    }
}
