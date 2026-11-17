plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val runNumber = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()

android {
    namespace = "com.vinicius.meular"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.vinicius.meular"
        minSdk = 24
        targetSdk = 34
        versionCode = runNumber
        versionName = "1.$runNumber"
    }

    signingConfigs {
        getByName("debug") {
            storeFile = file("meular.keystore")
            storePassword = "android"
            keyAlias = "meular"
            keyPassword = "android"
        }
    }

    buildTypes {
        getByName("debug") { signingConfig = signingConfigs.getByName("debug") }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    // malhas grandes da cidade ficam sem compressão no APK: o jogo lê direto delas, sem copiar 250 MB para o celular
    androidResources { noCompress += listOf("bin") }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("com.github.junrar:junrar:7.5.5")   // abrir .rar de mods
}
