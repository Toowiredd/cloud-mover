use eframe::egui;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::process::{Command, Stdio};
use std::thread;
use walkdir::WalkDir;
use indicatif::{ProgressBar, ProgressStyle};
use std::time::Duration;

#[derive(Clone)]
struct UploadState {
    total_files: u64,
    processed_files: u64,
    current_file: String,
    is_uploading: bool,
    status_message: String,
}

struct RCloneDropPortal {
    selected_folder: Option<PathBuf>,
    upload_state: Arc<Mutex<UploadState>>,
    show_advanced: bool,
    destination_path: String,
    parallel_transfers: i32,
    chunk_size: String,
}

impl Default for RCloneDropPortal {
    fn default() -> Self {
        Self {
            selected_folder: None,
            upload_state: Arc::new(Mutex::new(UploadState {
                total_files: 0,
                processed_files: 0,
                current_file: String::new(),
                is_uploading: false,
                status_message: "Ready to upload".to_string(),
            })),
            show_advanced: false,
            destination_path: "uploads".to_string(),
            parallel_transfers: 4,
            chunk_size: "128M".to_string(),
        }
    }
}

impl RCloneDropPortal {
    fn count_files(&self, path: &Path) -> u64 {
        WalkDir::new(path)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .count() as u64
    }

    fn start_upload(&mut self) {
        if let Some(folder) = &self.selected_folder {
            let folder = folder.clone();
            let state = self.upload_state.clone();
            let destination = self.destination_path.clone();
            let transfers = self.parallel_transfers;
            let chunk_size = self.chunk_size.clone();

            thread::spawn(move || {
                // Update state
                {
                    let mut state = state.lock().unwrap();
                    state.is_uploading = true;
                    state.status_message = "Counting files...".to_string();
                }

                // Count files
                let total_files = WalkDir::new(&folder)
                    .into_iter()
                    .filter_map(|e| e.ok())
                    .filter(|e| e.file_type().is_file())
                    .count() as u64;

                {
                    let mut state = state.lock().unwrap();
                    state.total_files = total_files;
                    state.processed_files = 0;
                    state.status_message = format!("Uploading {} files...", total_files);
                }

                // Build rclone command
                let folder_name = folder.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("upload");
                
                let dest = format!("gdrive:{}/{}", destination, folder_name);
                
                let output = Command::new("../rclone.exe")
                    .args(&[
                        "copy",
                        folder.to_str().unwrap(),
                        &dest,
                        "--progress",
                        "--transfers", &transfers.to_string(),
                        "--checkers", "8",
                        "--buffer-size", "32M",
                        "--drive-chunk-size", &chunk_size,
                        "--log-level", "INFO",
                        "--stats", "1s",
                        "--stats-one-line",
                    ])
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped())
                    .output();

                // Update final state
                {
                    let mut state = state.lock().unwrap();
                    state.is_uploading = false;
                    
                    match output {
                        Ok(result) => {
                            if result.status.success() {
                                state.status_message = format!("Successfully uploaded {} files to {}", total_files, dest);
                                state.processed_files = total_files;
                            } else {
                                let error = String::from_utf8_lossy(&result.stderr);
                                state.status_message = format!("Upload failed: {}", error);
                            }
                        }
                        Err(e) => {
                            state.status_message = format!("Failed to run rclone: {}", e);
                        }
                    }
                }
            });
        }
    }
}

impl eframe::App for RCloneDropPortal {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Request repaint for progress updates
        ctx.request_repaint_after(Duration::from_millis(100));

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.vertical_centered(|ui| {
                ui.heading("RClone Drop Portal");
                ui.label("Upload millions of files efficiently to Google Drive");
                ui.separator();
            });

            // Folder selection
            ui.horizontal(|ui| {
                ui.label("Selected folder:");
                if let Some(folder) = &self.selected_folder {
                    ui.label(folder.display().to_string());
                } else {
                    ui.label("None");
                }
                
                if ui.button("Browse...").clicked() {
                    if let Some(folder) = rfd::FileDialog::new().pick_folder() {
                        let file_count = self.count_files(&folder);
                        self.selected_folder = Some(folder);
                        
                        let mut state = self.upload_state.lock().unwrap();
                        state.status_message = format!("Selected folder contains {} files", file_count);
                    }
                }
            });

            ui.separator();

            // Advanced options
            ui.checkbox(&mut self.show_advanced, "Show advanced options");
            
            if self.show_advanced {
                ui.group(|ui| {
                    ui.horizontal(|ui| {
                        ui.label("Destination path:");
                        ui.text_edit_singleline(&mut self.destination_path);
                    });
                    
                    ui.horizontal(|ui| {
                        ui.label("Parallel transfers:");
                        ui.add(egui::Slider::new(&mut self.parallel_transfers, 1..=16));
                    });
                    
                    ui.horizontal(|ui| {
                        ui.label("Chunk size:");
                        ui.text_edit_singleline(&mut self.chunk_size);
                        ui.label("(e.g., 128M, 256M)");
                    });
                });
            }

            ui.separator();

            // Upload button and progress
            let state = self.upload_state.lock().unwrap();
            
            ui.horizontal(|ui| {
                if !state.is_uploading {
                    if ui.button("Start Upload").clicked() && self.selected_folder.is_some() {
                        drop(state);
                        self.start_upload();
                    }
                } else {
                    ui.label("Uploading...");
                    ui.spinner();
                }
            });

            // Progress bar
            if state.total_files > 0 {
                let progress = state.processed_files as f32 / state.total_files as f32;
                ui.add(egui::ProgressBar::new(progress)
                    .text(format!("{}/{} files", state.processed_files, state.total_files)));
            }

            // Status message
            ui.label(&state.status_message);

            // Current file
            if !state.current_file.is_empty() {
                ui.label(format!("Current: {}", state.current_file));
            }

            ui.separator();

            // Instructions
            ui.collapsing("Instructions", |ui| {
                ui.label("1. Click 'Browse' to select a folder");
                ui.label("2. Optionally configure advanced settings");
                ui.label("3. Click 'Start Upload' to begin");
                ui.label("4. Files will be uploaded to Google Drive in batches");
                ui.label("");
                ui.label("This tool is optimized for uploading millions of files efficiently.");
                ui.label("It uses parallel transfers and chunking to maximize performance.");
            });
        });
    }
}

fn main() -> Result<(), eframe::Error> {
    // Check if rclone is configured
    let output = Command::new("../rclone.exe")
        .args(&["listremotes"])
        .output()
        .expect("Failed to run rclone");
    
    let remotes = String::from_utf8_lossy(&output.stdout);
    if !remotes.contains("gdrive:") {
        eprintln!("Error: Google Drive not configured in rclone!");
        eprintln!("Please run: rclone config");
        eprintln!("And create a remote named 'gdrive'");
        std::process::exit(1);
    }

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([600.0, 500.0])
            .with_min_inner_size([400.0, 300.0]),
        ..Default::default()
    };

    eframe::run_native(
        "RClone Drop Portal",
        options,
        Box::new(|_cc| Box::new(RCloneDropPortal::default())),
    )
}