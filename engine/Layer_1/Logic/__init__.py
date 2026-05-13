"""
Logic orchestrator for Layer 1.

Aggregates all logic modules and produces a structured result
containing risks and overall status for each dimension.
"""
import logging

from engine.Layer_1.Logic.data_integrity_logic import run_data_integrity_logic
from engine.Layer_1.Logic.target_validity_logic import run_target_validity_logic
from engine.Layer_1.Logic.sample_adequacy_logic import run_sample_adequacy_logic
from engine.Layer_1.schema import SignalExtractionResult, LogicExtractionResult, Signal_Structure

logger = logging.getLogger(__name__)

def run_logic_extraction(signals: SignalExtractionResult) -> LogicExtractionResult:
    dimensions = {}
    
    # 1. Data Integrity
    if "data_integrity" in signals.dimensions:
        dimensions["data_integrity"] = run_data_integrity_logic(signals.dimensions["data_integrity"])

    # 2. Sample Adequacy
    if "sample_adequacy" in signals.dimensions:
        dimensions["sample_adequacy"] = run_sample_adequacy_logic(signals.dimensions["sample_adequacy"])

    # 3. Target Validity
    if "target_validity" in signals.dimensions:
        dimensions["target_validity"] = run_target_validity_logic(signals.dimensions["target_validity"])

    return LogicExtractionResult(dimensions=dimensions)


if __name__ == "__main__":
    mock_signals = SignalExtractionResult(
        dimensions={
            'data_integrity': [
                Signal_Structure(dimension='data_integrity', name='dataset_shape', value={'rows': 891, 'cols': 12}, status='ok', meta={'total_cells': 10692}),
                Signal_Structure(dimension='data_integrity', name='global_missing_ratio', value=0.08099513655069211, status='ok', meta={'total_cells': 10692}),
                Signal_Structure(dimension='data_integrity', name='column_missing_ratio', value={'per_column': {'PassengerId': 0.0, 'Survived': 0.0, 'Pclass': 0.0, 'Name': 0.0, 'Sex': 0.0, 'Age': 0.19865319865319866, 'SibSp': 0.0, 'Parch': 0.0, 'Ticket': 0.0, 'Fare': 0.0, 'Cabin': 0.7710437710437711, 'Embarked': 0.002244668911335578}, 'worst_ratio': 0.7710437710437711}, status='ok', meta={'num_columns': 12}),
                Signal_Structure(dimension='data_integrity', name='duplicated_ratio', value=0.0, status='ok', meta={'num_rows': 891}),
                Signal_Structure(dimension='data_integrity', name='constant_columns_ratio', value={'columns': [], 'ratio': 0.0}, status='ok', meta={'total_columns': 12}),
                Signal_Structure(dimension='data_integrity', name='hidden_missing_ratio', value={'ratios': {'Name': 0.0, 'Sex': 0.0, 'Ticket': 0.0, 'Cabin': 0.7710437710437711, 'Embarked': 0.002244668911335578}, 'worst_ratio': 0.7710437710437711}, status='ok', meta={'num_object_columns': 5}),
                Signal_Structure(dimension='data_integrity', name='mixed_type_columns_ratio', value={'columns': ['Ticket'], 'ratio': 0.2}, status='ok', meta={'num_object_columns': 5})
            ],
            'sample_adequacy': [
                Signal_Structure(dimension='sample_adequacy', name='duplicated_ratio', value=0.0, status='ok', meta={'total_rows': 891, 'duplicate_rows': 0, 'unique_rows': 891}),
                Signal_Structure(dimension='sample_adequacy', name='effective_sample_size', value=2.8023705022704237, status='ok', meta={'avg_nn_distance': 2.8023705022704237, 'sample_size_used': 500, 'total_rows': 891, 'feature_count': 14}),
                Signal_Structure(dimension='sample_adequacy', name='sample_dependency_score', value=11.466907040283509, status='ok', meta={'avg_step_distance': 11.466907040283509, 'total_rows': 891, 'feature_count': 14}),
                Signal_Structure(dimension='sample_adequacy', name='feature_variance_score', value=0.07142857142857142, status='ok', meta={'low_variance_ratio': 0.07142857142857142, 'low_variance_columns': ['Sex_nan'], 'low_variance_count': 1, 'total_features': 14, 'threshold_used': 0.0002326233622113772}),
                Signal_Structure(dimension='sample_adequacy', name='marginal_coverage', value=0.31428571428571417, status='ok', meta={'avg_bin_coverage': 0.31428571428571417, 'per_column_coverage': {'PassengerId': 1.0, 'Survived': 0.1, 'Pclass': 0.2, 'Age': 1.0, 'SibSp': 0.2, 'Parch': 0.3, 'Fare': 1.0, 'Sex_female': 0.1, 'Sex_male': 0.1, 'Sex_nan': 0.0, 'Embarked_C': 0.1, 'Embarked_Q': 0.1, 'Embarked_S': 0.1, 'Embarked_nan': 0.1}, 'bins_used': 10, 'columns_evaluated': 14}),
                Signal_Structure(dimension='sample_adequacy', name='joint_coverage', value=1.0, status='ok', meta={'grid_fill': 1.0, 'columns_used': ['PassengerId', 'Fare'], 'bins_used': 5, 'filled_cells': 25, 'total_cells': 25})
            ],
            'target_validity': [
                Signal_Structure(dimension='target_validity', name='target_column_name', value='Survived', status='ok', meta={'dtype': 'int64'}),
                Signal_Structure(dimension='target_validity', name='target_shape', value={'rows': 891, 'cols': 1}, status='ok', meta={'n_samples': 891}),
                Signal_Structure(dimension='target_validity', name='target_missing_ratio', value=0.0, status='ok', meta={'n_samples': 891, 'missing_count': 0}),
                Signal_Structure(dimension='target_validity', name='target_degeneracy_flag', value=False, status='ok', meta={'unique_values': 2}),
                Signal_Structure(dimension='target_validity', name='dominant_class_ratio', value=0.6161616161616161, status='ok', meta={'n_samples': 891, 'dominant_class': '0', 'dominant_count': 549, 'total_unique': 2, 'class_distribution': {'0': 0.6162, '1': 0.3838}}),
                Signal_Structure(dimension='target_validity', name='target_entropy', value=0.9607078989902569, status='ok', meta={'num_classes': 2, 'max_entropy': 1.0}),
                Signal_Structure(dimension='target_validity', name='type_contamination_ratio', value=0.0, status='ok', meta={'major_type': 'int', 'contaminated_count': 0, 'total_non_null': 891, 'type_breakdown': {'int': 891}})
            ]
        }
    )
    output = run_logic_extraction(mock_signals)
    
    print(output)