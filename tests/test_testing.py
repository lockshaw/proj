from proj.testing import (
    parse_test_case_output,
    DoctestTestCaseExecutionSuffix,
    strip_terminal_escapes,
)

def test_strip_terminal_escapes() -> None:
    example_input = b'\x1b[0;36m[doctest] \x1b[0mStatus: \x1b[0;32mSUCCESS!\x1b[0m'

    result = strip_terminal_escapes(example_input)
    correct = b'[doctest] Status: SUCCESS!'

    assert result == correct

def test_parse_test_case_output() -> None:
    example_output = b'\n'.join([
        br'===============================================================================',
        br'../../lib/op-attrs/test/src/op-attrs/ops/flat.cc:191:',
        br'TEST SUITE: cpu-op-attrs-tests',
        br'TEST CASE:  get_output_shape(FlatAttrs, ParallelTensorShape)',
        br'',
        br'../../lib/op-attrs/test/src/op-attrs/ops/flat.cc:191: ERROR: test case THREW exception: Assertion failed:',
        br'Assertion failed at ../lib/op-attrs/src/op-attrs/ops/flat.cc:46: FlexFlow::ParallelTensorDimDegrees FlexFlow::get_output_parallel_dim_degrees(const FlexFlow::FlatAttrs&, const FlexFlow::ParallelTensorDimDegrees&): get_output_parallel_dim_degrees for {} expected all shard degrees of flattened dimensions to be 1',
        br'    ASSERT(any_of(flattened_dim_degrees, [](positive_int degree) { return degree != 1; }), ...);',
        br'',
        br'Stack trace:',
        br'# 1 FlexFlow::get_output_parallel_dim_degrees(FlexFlow::FlatAttrs const&, FlexFlow::ParallelTensorDimDegrees const&)',
        br'      at lib/op-attrs/src/op-attrs/ops/flat.cc:46',
        br'# 2 FlexFlow::get_output_shape(FlexFlow::FlatAttrs const&, FlexFlow::ParallelTensorShape const&)',
        br'      at lib/op-attrs/src/op-attrs/ops/flat.cc:68',
        br'# 3 DOCTEST_ANON_FUNC_17',
        br'      at test/src/op-attrs/ops/flat.cc:219',
        br'# 4 doctest::Context::run()',
        br'      at doctest.h:6930',
        br'# 5 main',
        br'      at main.cc:16',
        br'',
        br'',
        br'===============================================================================',
        b'\x1b[0;36m[doctest] \x1b[0mtest cases: 1 | \x1b[0;32m0 passed\x1b[0m | \x1b[0m1 failed\x1b[0m | \x1b[0;33m84 skipped\x1b[0m',
        b'\x1b[0;36m[doctest] \x1b[0massertions: 3 | \x1b[0;32m3 passed\x1b[0m | \x1b[0m0 failed\x1b[0m |',
        b'\x1b[0;36m[doctest] \x1b[0mStatus: \x1b[0;32mFAILURE!\x1b[0m',
    ])

    result = parse_test_case_output(example_output)

    correct = DoctestTestCaseExecutionSuffix(
        test_cases_passed=0,
        test_cases_failed=1,
        test_cases_skipped=84,
        assertions_passed=3,
        assertions_failed=0,
        succeeded=False,
    )

    assert result == correct
