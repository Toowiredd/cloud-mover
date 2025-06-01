use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};
use walkdir::WalkDir;
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use rayon::prelude::*;

pub struct BulkUploader {
    source: PathBuf,
    destination: String,
    parallel_transfers: u32,
    chunk_size: String,
}

impl BulkUploader {
    pub fn new(source: PathBuf) -> Self {
        Self {
            source,
            destination: "uploads".to_string(),
            parallel_transfers: 16,
            chunk_size: "256M".to_string(),
        }
    }

    pub fn count_files_parallel(&self) -> u64 {
        let count = AtomicU64::new(0);
        
        WalkDir::new(&self.source)
            .into_iter()
            .par_bridge()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .for_each(|_| {
                count.fetch_add(1, Ordering::Relaxed);
            });
        
        count.load(Ordering::Relaxed)
    }

    pub fn upload(&self) -> Result<(), Box<dyn std::error::Error>> {
        let multi_progress = MultiProgress::new();
        
        // File counting progress
        let count_pb = multi_progress.add(ProgressBar::new_spinner());
        count_pb.set_style(
            ProgressStyle::default_spinner()
                .template("{spinner:.green} {msg}")
                .unwrap()
        );
        count_pb.set_message("Counting files...");
        
        let start = Instant::now();
        let total_files = self.count_files_parallel();
        count_pb.finish_with_message(format!("Found {} files in {:?}", total_files, start.elapsed()));
        
        // Upload progress
        let upload_pb = multi_progress.add(ProgressBar::new(100));
        upload_pb.set_style(
            ProgressStyle::default_bar()
                .template("{spinner:.green} [{bar:40.cyan/blue}] {pos}% | {msg}")
                .unwrap()
                .progress_chars("#>-")
        );
        upload_pb.set_message("Starting upload...");
        
        // Build rclone command
        let folder_name = self.source.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("upload");
        
        let dest = format!("gdrive:{}/{}", self.destination, folder_name);
        
        let mut cmd = Command::new("../rclone.exe")
            .args(&[
                "copy",
                self.source.to_str().unwrap(),
                &dest,
                "--transfers", &self.parallel_transfers.to_string(),
                "--checkers", "16",
                "--buffer-size", "32M",
                "--drive-chunk-size", &self.chunk_size,
                "--drive-upload-cutoff", &self.chunk_size,
                "--fast-list",
                "--no-check-dest",
                "--no-update-modtime",
                "--drive-use-trash=false",
                "--low-level-retries", "10",
                "--retries", "5",
                "--stats", "2s",
                "--stats-one-line",
                "--log-level", "INFO",
                "--progress",
            ])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        // Monitor progress
        let status = cmd.wait()?;
        
        if status.success() {
            upload_pb.finish_with_message(format!("Successfully uploaded {} files to {}", total_files, dest));
            Ok(())
        } else {
            Err("Upload failed".into())
        }
    }
}

// CLI entry point
pub fn run_cli(args: Vec<String>) {
    if args.len() < 2 {
        eprintln!("Usage: {} <folder_path>", args[0]);
        std::process::exit(1);
    }
    
    let source = PathBuf::from(&args[1]);
    if !source.exists() || !source.is_dir() {
        eprintln!("Error: '{}' is not a valid directory", source.display());
        std::process::exit(1);
    }
    
    println!("RClone Bulk Uploader - Optimized for millions of files");
    println!("=====================================================");
    println!();
    
    let uploader = BulkUploader::new(source);
    
    match uploader.upload() {
        Ok(()) => {
            println!("\nUpload completed successfully!");
        }
        Err(e) => {
            eprintln!("\nUpload failed: {}", e);
            std::process::exit(1);
        }
    }
}