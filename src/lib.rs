use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::Instant;

#[pyclass]
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct WordStats {
    pub words: usize,
    pub characters: usize,
    pub characters_no_spaces: usize,
    pub sentences: usize,
    pub paragraphs: usize,
    pub unique_words: usize,
    pub avg_word_length: f64,
    pub reading_time_seconds: usize,
    pub density: HashMap<String, f64>,
    pub top_words: Vec<(String, usize)>,
    pub longest_words: Vec<String>,
}

#[pymethods]
impl WordStats {
    #[new]
    pub fn new() -> Self {
        WordStats {
            words: 0,
            characters: 0,
            characters_no_spaces: 0,
            sentences: 0,
            paragraphs: 0,
            unique_words: 0,
            avg_word_length: 0.0,
            reading_time_seconds: 0,
            density: HashMap::new(),
            top_words: Vec::new(),
            longest_words: Vec::new(),
        }
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_else(|_| "{}".to_string())
    }
}

impl WordStats {
    pub fn analyze(&mut self, text: &str) {
        // Character counts
        self.characters = text.chars().count();
        self.characters_no_spaces = text.chars()
            .filter(|c| !c.is_whitespace())
            .count();
        
        // Split into paragraphs
        let paragraphs: Vec<&str> = text
            .split("\n\n")
            .filter(|p| !p.trim().is_empty())
            .collect();
        self.paragraphs = paragraphs.len();
        
        // Sentence detection
        let sentence_re = regex::Regex::new(r"[.!?]+[\s\n]+").unwrap();
        let sentences: Vec<&str> = sentence_re
            .split(text)
            .filter(|s| !s.trim().is_empty())
            .collect();
        self.sentences = sentences.len();
        
        // Word detection
        let word_re = regex::Regex::new(r"\b[\p{L}\p{M}']+(?:-[\p{L}\p{M}']+)*\b").unwrap();
        let words: Vec<String> = word_re.find_iter(text)
            .map(|m| m.as_str().to_lowercase())
            .collect();
        
        self.words = words.len();
        
        // Calculate average word length
        let total_letters: usize = words.iter()
            .map(|w| w.chars().filter(|c| c.is_alphabetic()).count())
            .sum();
        self.avg_word_length = if self.words > 0 {
            total_letters as f64 / self.words as f64
        } else { 0.0 };
        
        // Unique words
        let mut word_counts = HashMap::new();
        for word in &words {
            *word_counts.entry(word.clone()).or_insert(0) += 1;
        }
        self.unique_words = word_counts.len();
        
        // Top 5 most frequent words
        let mut word_vec: Vec<(String, usize)> = word_counts.into_iter().collect();
        word_vec.sort_by(|a, b| b.1.cmp(&a.1));
        self.top_words = word_vec.iter()
            .take(5)
            .map(|(word, count)| (word.clone(), *count))
            .collect();
        
        // Longest words
        let mut unique_words_set: Vec<String> = words.into_iter().collect();
        unique_words_set.sort();
        unique_words_set.dedup();
        unique_words_set.sort_by_key(|w| std::cmp::Reverse(w.len()));
        self.longest_words = unique_words_set.into_iter().take(5).collect();
        
        // Reading time (225 WPM)
        self.reading_time_seconds = (self.words as f64 / 225.0 * 60.0) as usize;
    }
}

#[pyfunction]
pub fn analyze_text_fast(text: &str) -> WordStats {
    let mut stats = WordStats::new();
    stats.analyze(text);
    stats
}

#[pymodule]
fn wdlib(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(analyze_text_fast, m)?)?;
    m.add_class::<WordStats>()?;
    Ok(())
}