
def analyze_minimax(distance_storages: List[Distances], filenames: List[str]):
    print("\n" + "="*60)
    print("MINIMAX CENTER ANALYSIS")
    print("="*60)
    
    for storage in distance_storages:
        algo_name = storage._algo_name
        print(f"\nAlgorithm: {algo_name}")
        
        try:
            center_idx, min_max_distance, max_distances = storage.find_minimax_center()
            center_filename = filenames[center_idx]
        
            print(f"Most centered text: {center_filename}")
            print(f"Minimax distance: {min_max_distance:.4f}")
            print(f"Center index: {center_idx}")
            
            # Show top 5 most centered texts
            sorted_distances = sorted(max_distances.items(), key=lambda x: x[1])
            print(f"\nTop 5 most centered texts:")
            for i, (idx, max_dist) in enumerate(sorted_distances[:5]):
                filename = filenames[idx]
                print(f"  {i+1}. {filename} (max distance: {max_dist:.4f})")
                
        except Exception as e:
            print(f"Error in minimax analysis for {algo_name}: {e}")