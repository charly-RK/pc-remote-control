buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        // Necesario para habilitar desugaring en Kotlin DSL
        classpath("com.android.tools:r8:8.3.37")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory = rootProject.layout.buildDirectory.dir("../../build").get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

subprojects {
    project.evaluationDependsOn(":app")
}

subprojects {
    if (project.name == "flutter_vibrate") {
        fun configureNamespace() {
            try {
                project.extensions.configure<com.android.build.gradle.LibraryExtension> {
                    namespace = "flutter.plugins.vibrate"
                }
            } catch (e: Exception) {
                // Ignore
            }
        }

        if (project.state.executed) {
            configureNamespace()
        } else {
            project.afterEvaluate {
                configureNamespace()
            }
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
