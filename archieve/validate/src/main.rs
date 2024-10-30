use std::env;
use std::fs;
use std::path::Path;
use std::collections::HashMap;
use serde_json::Value;
use std::process;
use regex::Regex;

// Longest Common Subsequence Function
fn lcs(s1: &Vec<&str>, s2: &Vec<&str>) -> usize {
    let n1 = s1.len();
    let n2 = s2.len();
    let mut dp = vec![vec![0; n2 + 1]; n1 + 1];

    for i in 1..=n1 {
        for j in 1..=n2 {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    dp[n1][n2]
}

fn main() {
    // --- Start of Test Code for LCS Function ---
    // Equivalent to:
    // str1 = "This is a test"
    // str2 = "This is not a test"
    // print(lcs(str1.split(), str2.split()))

    let str1 = "This is a test";
    let str2 = "This is not a test";

    let s1: Vec<&str> = str1.split_whitespace().collect();
    let s2: Vec<&str> = str2.split_whitespace().collect();

    let result = lcs(&s1, &s2);
    println!("LCS length between '{} and '{}': {}", str1, str2, result);
    // --- End of Test Code for LCS Function ---

    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Please provide a path as a command-line argument.");
        process::exit(1);
    }

    let path = &args[1];
    if !Path::new(path).exists() {
        eprintln!("The path does not exist");
        process::exit(1);
    }

    let mut datasets = Vec::new();
    let dir_list = fs::read_dir(path).expect("Failed to read directory");
    
    for entry in dir_list {
        let entry = entry.expect("Failed to read entry");
        let file_path = entry.path();
        let file_data = fs::read_to_string(&file_path).expect("Failed to read file");

        let data: Vec<Value> = serde_json::from_str(&file_data).expect("Failed to parse JSON");
        datasets.push(data);
    }

    let mut results_article: HashMap<(usize, usize), Vec<f64>> = HashMap::new();
    let mut results_answer: HashMap<(usize, usize), Vec<f64>> = HashMap::new();

    let re = Regex::new(r"(\d+)").unwrap();

    for i in 0..datasets.len() {
        for j in (i + 1)..datasets.len() {
            let filename_i = datasets[i][0]["filename"].to_string();
            let file_i = re.captures(&filename_i)
                           .and_then(|cap| cap.get(1).map(|m| m.as_str()))
                           .unwrap_or("Unknown");
            
            let filename_j = datasets[j][0]["filename"].to_string();
            let file_j = re.captures(&filename_j)
                           .and_then(|cap| cap.get(1).map(|m| m.as_str()))
                           .unwrap_or("Unknown");

            println!("Comparing dataset {} with dataset {}", file_i, file_j);

            for data in &datasets[i] {
                let article: Vec<&str> = data["article"].as_str().unwrap().split_whitespace().collect();
                let answer: Vec<&str> = data["answer"].as_str().unwrap().split_whitespace().collect();

                let max_article_lcs = datasets[j]
                    .iter()
                    .map(|data2| lcs(&article, &data2["article"].as_str().unwrap().split_whitespace().collect::<Vec<&str>>()))
                    .max()
                    .unwrap_or(0);

                let max_answer_lcs = datasets[j]
                    .iter()
                    .map(|data2| lcs(&answer, &data2["answer"].as_str().unwrap().split_whitespace().collect::<Vec<&str>>()))
                    .max()
                    .unwrap_or(0);

                results_article
                    .entry((i, j))
                    .or_insert_with(Vec::new)
                    .push(max_article_lcs as f64 / article.len() as f64);
                results_answer
                    .entry((i, j))
                    .or_insert_with(Vec::new)
                    .push(max_answer_lcs as f64 / answer.len() as f64);

                for data2 in &datasets[j] {
                    let article2 = data2["article"].as_str().unwrap();
                    let answer2 = data2["answer"].as_str().unwrap();

                    if article.join(" ") == article2 {
                        println!("Duplicate article found");
                        process::exit(1);
                    }

                    if answer.join(" ") == answer2 {
                        println!("Duplicate answer found");
                        process::exit(1);
                    }
                }
            }

            println!(
                "Article similarity, dataset({}, {}): {:.2}",
                file_i,
                file_j,
                results_article[&(i, j)].iter().cloned().fold(0.0, f64::max)
            );
            println!(
                "Answer similarity, dataset({}, {}): {:.2}",
                file_i,
                file_j,
                results_answer[&(i, j)].iter().cloned().fold(0.0, f64::max)
            );
        }
    }
}

/*
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lcs() {
        let str1 = "This is a test";
        let str2 = "This is not a test";
        
        let s1: Vec<&str> = str1.split_whitespace().collect();
        let s2: Vec<&str> = str2.split_whitespace().collect();
        
        let result = lcs(&s1, &s2);
        assert_eq!(result, 4);  // The LCS should be 4, as "This is a test" is common between them
        println!("Test passed");
    }
}
*/