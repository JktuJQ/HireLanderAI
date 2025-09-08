def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--example", dest="example", type=str, required=False,
                        help="Run file for testing purposes")
    args = parser.parse_args()

    if args.example is not None:
        try:
            exec(f"import examples.{args.example}")
        except ImportError as e:
            print(f"There is no `examples/{args.example}.py` test file ({e})")
        except Exception as e:
            print(e, type(e))
        finally:
            exit()
    else:
        pass


if __name__ == "__main__":
    main()
